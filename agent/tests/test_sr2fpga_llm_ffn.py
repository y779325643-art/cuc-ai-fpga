"""Exact integer FFN controls, PC construction and evaluator-owned HDL checks."""

from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import json
import random

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.local_tools import resolve_executable
from sr2fpga_agent.pc.checker import check_design
from sr2fpga_agent.pc.development_tools import run_recorded
from sr2fpga_agent.pc.emitter import build_structure, compose_behavior, write_project
from sr2fpga_agent.tasks.llm_ffn import build_development_task, reference_design
from sr2fpga_agent.tasks.llm_ffn.harness import check_trace, development_frames, render_testbench
from sr2fpga_agent.tasks.llm_ffn.oracle import evaluate, nearest_even, pack_tensor, unpack_tensor
from sr2fpga_agent.tasks.llm_ffn.reference import reference_behavior_bodies, render_reference_project
from sr2fpga_agent.tasks.llm_ffn.task import (
    GATE_WEIGHTS, UP_WEIGHTS, DOWN_WEIGHTS, GATE_BIAS, UP_BIAS, DOWN_BIAS,
    SILU_LUT, COMPLETION_CYCLES,
)


def _build():
    task = build_development_task()
    checked = check_design(reference_design(), task["boundary"]["boundary"],
                           task["capability_profile"]["limits"], facts=task["facts"],
                           public_assets=task["public_assets"])
    bindings = {name: {"id": name, "sha256": "0" * 64}
                for name in ("requirements", "target_profile", "capability_profile")}
    return build_structure(checked, bindings=bindings)


def test_public_ffn_is_typed_and_has_only_public_assets():
    task = build_development_task()
    registry = ContractRegistry()
    for contract, document in (("development_public_boundary", task["boundary"]),
                               ("pc21_development_target", task["target_profile"]),
                               ("pc21_development_capability", task["capability_profile"]),
                               ("design_proposal_2_1", reference_design())):
        assert not registry.load_schema(contract).validate(document)
    assert task["development_only"] is True
    assert task["family"] == "llm_gated_ffn"
    assert not {"oracle", "harness", "expected", "test_frames"} & set(task)
    constants = json.loads(task["public_assets"]["ffn_constants"])
    assert len(constants["silu_lut"]) == 256
    build = _build()
    assert {unit["module_id"] for unit in build.units.values()} == {
        "FfnInputFork", "FfnGateUp", "FfnFuseDownResidual"}
    assert len(build.files) == 1


def test_frozen_lut_matches_its_public_generation_rule():
    with localcontext() as context:
        context.prec = 70
        expected = tuple(max(-128, min(127, int((Decimal(q) / (1 + (-Decimal(q) / 4).exp())).quantize(
            Decimal(1), rounding=ROUND_HALF_EVEN)))) for q in range(-128, 128))
    assert SILU_LUT == expected
    assert [SILU_LUT[q + 128] for q in (-128, -12, -8, -4, -1, 0, 1, 4, 8, 12, 16, 127)] == [
        0, -1, -1, -1, 0, 0, 1, 3, 7, 11, 16, 127]


@pytest.mark.parametrize("value,expected", [(2, 0), (6, 2), (10, 2), (-2, 0), (-6, -2), (-10, -2)])
def test_signed_rounding_half_ties(value, expected):
    assert nearest_even(value, 4) == expected


def test_hand_golden_bias_residual_gate_and_tail():
    # At x=0 every requantized gated product is zero; down bias alone yields
    # [round(3/4), round(-1/4), round(5/4), round(-5/4), round(1/4)].
    assert evaluate((0,) * 10) == (1, 0, 1, -1, 0) * 2
    # x=[4,0,0,0,0] makes only product channel1=-1; then add x after down RNE.
    assert evaluate((4, 0, 0, 0, 0) * 2) == (5, 0, 1, -2, 0) * 2
    assert pack_tensor((-128, 127, -1, 0, 2)) == (0x37F80, 0x300FF, 0x10002)
    assert unpack_tensor((0x37F80, 0x300FF, 0x10002)) == (-128, 127, -1, 0, 2)
    with pytest.raises(ValueError, match="tail lane"):
        unpack_tensor((0x37F80, 0x300FF, 0x10102))


def test_distinct_columnwise_reference_and_token_identity():
    def r4(value):
        magnitude, remainder = divmod(abs(value), 4)
        rounded = magnitude + (remainder > 2 or remainder == 2 and magnitude % 2 == 1)
        return -rounded if value < 0 else rounded
    def sat(value):
        return min(127, max(-128, value))
    def cross(values):
        result = []
        for base in (0, 5):
            g, u = list(GATE_BIAS), list(UP_BIAS)
            for column, raw in enumerate(values[base:base + 5]):
                for row in range(7):
                    g[row] += raw * GATE_WEIGHTS[row][column]
                    u[row] += raw * UP_WEIGHTS[row][column]
            product = [sat(r4(SILU_LUT[sat(r4(a)) + 128] * sat(r4(b)))) for a, b in zip(g, u)]
            acc = list(DOWN_BIAS)
            for column, raw in enumerate(product):
                for row in range(5):
                    acc[row] += raw * DOWN_WEIGHTS[row][column]
            result.extend(sat(r4(acc[row]) + values[base + row]) for row in range(5))
        return tuple(result)
    rng = random.Random(723)
    for values in (*development_frames(), *(tuple(rng.randrange(-128, 128) for _ in range(10)) for _ in range(30))):
        assert evaluate(values) == cross(values)
        assert evaluate(values[5:] + values[:5]) == evaluate(values)[5:] + evaluate(values)[:5]
    for rows, biases in ((GATE_WEIGHTS, GATE_BIAS), (UP_WEIGHTS, UP_BIAS), (DOWN_WEIGHTS, DOWN_BIAS)):
        assert all(128 * sum(abs(x) for x in row) + abs(bias) < 2**31 for row, bias in zip(rows, biases))


def _complete_trace(final_cycle):
    inputs = pack_tensor((0,) * 10)
    outputs = pack_tensor(evaluate((0,) * 10))
    rows = []
    def emit(iv=0, ip=0, ov=0, op=0):
        rows.append(f"TRACE {len(rows) + 1} 1 {iv} 1 {ip:05x} {ov} 1 {op:05x}")
    for beat in inputs:
        emit(iv=1, ip=beat)
    for beat in outputs[:-1]:
        emit(ov=1, op=beat)
    while len(rows) < final_cycle - 1:
        emit()
    emit(ov=1, op=outputs[-1])
    return "\n".join(rows + [f"TRACE_END {len(rows)}"])


def test_monitor_last_beat_deadline_boundary_and_fake_pass():
    result = check_trace(_complete_trace(COMPLETION_CYCLES + 1), expected_completed=1)
    assert result.completed_invocations == 1
    with pytest.raises(ValueError, match="completion exceeded"):
        check_trace(_complete_trace(COMPLETION_CYCLES + 2), expected_completed=1)
    with pytest.raises(ValueError, match="incomplete"):
        check_trace("TEST_PASS\n")
    with pytest.raises(ValueError, match="output mismatch"):
        check_trace(_complete_trace(30).replace(" 1 1 30001", " 1 1 30000", 1), expected_completed=1)


@pytest.mark.parametrize("overlap", [False, True])
def test_monitor_accepts_token_streaming_with_optional_input_output_overlap(overlap):
    frame = (4, 0, 0, 0, 0, -3, 7, 1, -2, 9)
    inputs, outputs = pack_tensor(frame), pack_tensor(evaluate(frame))
    lines = []
    def emit(input_beat=None, output_beat=None):
        iv, ov = int(input_beat is not None), int(output_beat is not None)
        lines.append(f"TRACE {len(lines) + 1} 1 {iv} 1 {input_beat or 0:05x} {ov} 1 {output_beat or 0:05x}")
    for beat in inputs[:3]:
        emit(input_beat=beat)
    if overlap:
        for input_beat, output_beat in zip(inputs[3:], outputs[:3]):
            emit(input_beat=input_beat, output_beat=output_beat)
    else:
        for beat in outputs[:3]:
            emit(output_beat=beat)
        for beat in inputs[3:]:
            emit(input_beat=beat)
    for beat in outputs[3:]:
        emit(output_beat=beat)
    lines.append(f"TRACE_END {len(lines)}")
    result = check_trace("\n".join(lines), expected_completed=1)
    assert result.input_beats == result.output_beats == 6


def test_monitor_rejects_next_invocation_before_last_output_acceptance():
    lines = _complete_trace(30).splitlines()
    # Six inputs and only five outputs have transferred by cycle11. A seventh
    # accepted input at cycle12 belongs to a forbidden overlapping invocation.
    lines[11] = f"TRACE 12 1 1 1 {pack_tensor((0,) * 10)[0]:05x} 0 1 00000"
    with pytest.raises(ValueError, match="new input before previous output completed"):
        check_trace("\n".join(lines), expected_completed=1)


@pytest.mark.skipif(resolve_executable("yosys") is None, reason="real Yosys required")
def test_ffn_real_parser_composes_all_behavior_units(tmp_path):
    build = _build()
    bodies = reference_behavior_bodies()
    bundle = {"contract_version": "pc21-behavior-bundle-v1", "build_plan_sha256": build.build_plan_sha256,
              "units": {unit: {"body": bodies[metadata["module_id"]]} for unit, metadata in build.units.items()}}
    project = compose_behavior(build, bundle, scratch_root=tmp_path / "parser",
                               behavior_origin="hand_authored_development_control")
    write_project(project, tmp_path / "fpp")
    assert len(project.files) == 5
    assert all(record["returncode"] == 0 for record in project.parser_evidence.values())


@pytest.mark.skipif(not resolve_executable("iverilog") or not resolve_executable("vvp"),
                    reason="real Icarus and vvp required")
def test_ffn_real_hdl_math_stalls_reset_and_trace_corruption(tmp_path):
    sources = render_reference_project()
    sources["trusted_llm_ffn_tb.sv"] = render_testbench()
    for name, source in sources.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    compiled = run_recorded([str(resolve_executable("iverilog")), "-v", "-g2012", "-s", "trusted_llm_ffn_tb",
                             "-o", "simulation.vvp", *sources], tmp_path, "compile", timeout_seconds=30)
    (tmp_path / "compile.json").write_text(json.dumps(asdict(compiled), indent=2), encoding="utf-8")
    assert compiled.status == "passed", asdict(compiled)
    simulated = run_recorded([str(resolve_executable("vvp")), "simulation.vvp"],
                             tmp_path, "simulation", timeout_seconds=30)
    (tmp_path / "simulation.json").write_text(json.dumps(asdict(simulated), indent=2), encoding="utf-8")
    assert simulated.status == "passed", asdict(simulated)
    result = check_trace(simulated.stdout)
    assert result.completed_invocations == 3 and result.output_beats == 18
    assert result.resets == 3 and result.cancelled_invocations == 2
    lines = simulated.stdout.splitlines()
    for index, line in enumerate(lines):
        fields = line.split()
        if len(fields) == 9 and fields[0] == "TRACE" and fields[2] == fields[6] == fields[7] == "1":
            fields[8] = f"{int(fields[8], 16) ^ 1:05x}"
            lines[index] = " ".join(fields)
            break
    with pytest.raises(ValueError, match="output mismatch"):
        check_trace("\n".join(lines) + "\nTEST_PASS\n")
