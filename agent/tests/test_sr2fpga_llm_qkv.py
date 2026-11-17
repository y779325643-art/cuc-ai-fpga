"""Independent math, packing, PC construction and real HDL QKV controls."""

from __future__ import annotations

from dataclasses import asdict
import json
import random

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.local_tools import resolve_executable
from sr2fpga_agent.pc.checker import check_design
from sr2fpga_agent.pc.emitter import build_structure, compose_behavior, write_project
from sr2fpga_agent.tasks.llm_qkv import build_development_task, reference_design
from sr2fpga_agent.tasks.llm_qkv.harness import TESTBENCH_TOP, check_trace, render_testbench
from sr2fpga_agent.tasks.llm_qkv.oracle import evaluate, pack_tensor, packed_outputs, unpack_tensor
from sr2fpga_agent.tasks.llm_qkv.reference import reference_behavior_bodies, render_reference_project
from sr2fpga_agent.tasks.llm_qkv.task import WEIGHTS, BIASES, OUTPUT_DENOMINATORS, OUTPUT_ZEROS
from sr2fpga_agent.tool_runner import CommandRunner


def _build():
    task = build_development_task()
    checked = check_design(reference_design(), task["boundary"]["boundary"],
                           task["capability_profile"]["limits"], facts=task["facts"],
                           public_assets=task["public_assets"])
    bindings = {name: {"id": name, "sha256": "0" * 64}
                for name in ("requirements", "target_profile", "capability_profile")}
    return build_structure(checked, bindings=bindings)


def test_qkv_public_contract_and_head_shapes():
    task = build_development_task()
    registry = ContractRegistry()
    assert not registry.load_schema("development_public_boundary").validate(task["boundary"])
    assert not registry.load_schema("pc21_development_target").validate(task["target_profile"])
    assert not registry.load_schema("pc21_development_capability").validate(task["capability_profile"])
    assert not registry.load_schema("design_proposal_2_1").validate(reference_design())
    contracts = task["boundary"]["boundary"]["signature"]["tensor_contracts"]
    assert [axis["extent"] for axis in contracts["Q"]["shape"]] == [2, 4, 3]
    assert [axis["extent"] for axis in contracts["K"]["shape"]] == [2, 2, 3]
    assert [axis["extent"] for axis in contracts["V"]["shape"]] == [2, 2, 3]
    assert "oracle" not in task and "frames" not in task and "expected" not in task
    assert task["development_only"] is True
    assert len(_build().units) == 4


def test_zero_point_and_asymmetric_impulse_hand_goldens():
    baseline = evaluate((-2,) * 10)
    assert baseline == {
        "q": (-1, 1, 3, 1, 3, -1, 5, -3, 5, -3, 7, -5) * 2,
        "k": (-1, -1, 1, 0, -3, 1) * 2,
        "v": (3, 5, 1, 5, 1, 7) * 2,
    }
    impulse = evaluate((3,) + (-2,) * 9)
    assert impulse["q"][:12] == (2, -1, 9, 1, 5, -7, 12, -5, 11, -9, 7, -2)
    assert impulse["k"][:6] == (-2, 1, 1, 1, -6, 3)
    assert impulse["v"][:6] == (5, -1, 9, 3, 5, 7)
    assert impulse["q"][12:] == baseline["q"][12:]


def test_independent_signed_divmod_projection_and_saturation():
    def rne(value, divisor):
        quotient, remainder = divmod(abs(value), divisor)
        quotient += int(2 * remainder > divisor or 2 * remainder == divisor and quotient % 2 == 1)
        return -quotient if value < 0 else quotient

    rng = random.Random(293)
    frames = [tuple(rng.randrange(-128, 128) for _ in range(10)) for _ in range(20)]
    frames += [(127, -128, 127, -128, 127) * 2]
    saturated = False
    for frame in frames:
        actual = evaluate(frame)
        for branch, matrix in WEIGHTS.items():
            expected = []
            for token in (frame[:5], frame[5:]):
                centered = tuple(value + 2 for value in token)
                for row_index, row in enumerate(matrix):
                    acc = sum(centered[column] * row[column] for column in range(5)) + BIASES[branch][row_index]
                    assert abs(acc) < 2**31
                    output = max(-128, min(127, rne(acc, OUTPUT_DENOMINATORS[branch]) + OUTPUT_ZEROS[branch]))
                    saturated |= output in (-128, 127)
                    expected.append(output)
            assert actual[branch] == tuple(expected)
    assert saturated


@pytest.mark.parametrize("values", [(), (1,) * 9, (1,) * 11, (True,) * 10, (128,) * 10])
def test_oracle_rejects_invalid_input_domain(values):
    with pytest.raises(ValueError):
        evaluate(values)


def test_head_tails_and_physical_byte_goldens():
    assert pack_tensor((-128, 127, -1), 3) == (0x37F80, 0x100FF)
    assert pack_tensor((1, 2, 3, 4, 5, 6), 3) == (0x30201, 0x10003, 0x30504, 0x10006)
    assert unpack_tensor((0x37F80, 0x100FF), 3) == (-128, 127, -1)
    with pytest.raises(ValueError, match="invalid mask"):
        unpack_tensor((0x37F80, 0x101FF), 3)
    beats = packed_outputs((-2,) * 10)
    assert {branch: len(values) for branch, values in beats.items()} == {"q": 16, "k": 8, "v": 8}


def _trace(final_cycle=40):
    inputs = pack_tensor((-2,) * 10, 5)
    outputs = packed_outputs((-2,) * 10)
    lines = []
    cycle = 0

    def emit(iv=0, ip=0, offered=None):
        nonlocal cycle
        cycle += 1
        offered = offered or {}
        fields = ["TRACE", str(cycle), "1", str(iv), "1", f"{ip:05x}"]
        for branch in ("q", "k", "v"):
            value = offered.get(branch)
            fields += [str(int(value is not None)), "1", f"{value:05x}" if value is not None else "xxxxx"]
        lines.append(" ".join(fields))

    for value in inputs:
        emit(iv=1, ip=value)
    for index in range(15):
        emit(offered={branch: values[index] for branch, values in outputs.items() if index < len(values)})
    while cycle < final_cycle - 1:
        emit()
    emit(offered={"q": outputs["q"][-1]})
    lines.append("TRACE_END " + str(cycle))
    return "\n".join(lines)


def test_complete_trace_checks_output_and_final_deadline_boundary():
    assert check_trace(_trace(), expected_completed=1).output_beats == {"q": 16, "k": 8, "v": 8}
    assert check_trace(_trace(513), expected_completed=1).completed_invocations == 1
    with pytest.raises(ValueError, match="bounded completion"):
        check_trace(_trace(514), expected_completed=1)
    with pytest.raises(ValueError, match="incomplete"):
        check_trace("TEST_PASS\n")
    damaged = _trace().splitlines()
    fields = damaged[6].split()
    fields[8] = f"{int(fields[8], 16) ^ 1:05x}"
    damaged[6] = " ".join(fields)
    with pytest.raises(ValueError, match="wrong q"):
        check_trace("\n".join(damaged), expected_completed=1)


def test_monitor_accepts_token_streaming_before_full_frame_arrives():
    inputs = pack_tensor((-2,) * 5, 5)
    outputs = {branch: pack_tensor(values, 3)
               for branch, values in evaluate((-2,) * 10).items()}
    # Each token has half of each invocation's branch outputs. Emit all of
    # token zero before offering token one's inputs, unlike the RTL control.
    lines = []
    cycle = 0
    for token in range(2):
        for beat in inputs:
            cycle += 1
            lines.append(f"TRACE {cycle} 1 1 1 {beat:05x} 0 1 xxxxx 0 1 xxxxx 0 1 xxxxx")
        for index in range(8):
            cycle += 1
            fields = ["TRACE", str(cycle), "1", "0", "1", "xxxxx"]
            for branch in ("q", "k", "v"):
                per_token = len(outputs[branch]) // 2
                value = outputs[branch][token * per_token + index] if index < per_token else None
                fields += [str(int(value is not None)), "1", f"{value:05x}" if value is not None else "xxxxx"]
            lines.append(" ".join(fields))
    lines.append(f"TRACE_END {cycle}")
    assert check_trace("\n".join(lines), expected_completed=1).completed_invocations == 1


@pytest.mark.skipif(resolve_executable("yosys") is None, reason="real Yosys unavailable")
def test_qkv_reference_composition_real_parser(tmp_path):
    build = _build()
    bodies = reference_behavior_bodies()
    bundle = {"contract_version": "pc21-behavior-bundle-v1", "build_plan_sha256": build.build_plan_sha256,
              "units": {unit: {"body": bodies[metadata["module_id"]]} for unit, metadata in build.units.items()}}
    project = compose_behavior(build, bundle, scratch_root=tmp_path / "parser",
                               behavior_origin="hand_authored_development_control")
    assert len(project.files) == 6
    assert len(project.parser_evidence) == 5
    write_project(project, tmp_path / "project")


def _simulate_qkv(files, tmp_path):
    files["trusted_qkv_tb.sv"] = render_testbench()
    for name, content in files.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    runner = CommandRunner()
    compilation = runner.run(["iverilog", "-v", "-g2012", "-s", TESTBENCH_TOP,
                              "-o", "simulation.vvp", *files], tmp_path, "compile")
    (tmp_path / "compile.json").write_text(json.dumps(asdict(compilation), indent=2), encoding="utf-8")
    assert compilation.status == "passed", asdict(compilation)
    simulation = runner.run(["vvp", "simulation.vvp"], tmp_path, "simulate")
    (tmp_path / "simulation.json").write_text(json.dumps(asdict(simulation), indent=2), encoding="utf-8")
    assert simulation.status == "passed", asdict(simulation)
    trace = check_trace(simulation.stdout)
    assert trace.completed_invocations == 3
    assert trace.output_beats == {"q": 48, "k": 24, "v": 24}
    assert trace.resets == 3 and trace.cancelled_invocations == 2
    return simulation.stdout


@pytest.mark.skipif(not resolve_executable("iverilog") or not resolve_executable("vvp"), reason="Icarus/vvp unavailable")
def test_qkv_manual_reference_hdl(tmp_path):
    _simulate_qkv(render_reference_project(), tmp_path)


@pytest.mark.skipif(not resolve_executable("iverilog") or not resolve_executable("vvp"), reason="Icarus/vvp unavailable")
def test_qkv_token_streaming_reference_hdl_does_not_deadlock_reset_probe(tmp_path):
    stdout = _simulate_qkv(render_reference_project(tokens_per_batch=1), tmp_path)
    # The second reset episode must cancel a pending output while fewer than
    # six input beats have been accepted. This verifies the architecture-sensitive
    # driver schedule through actual clocked RTL rather than source inspection.
    episode = 0
    was_reset = False
    accepted = 0
    observed_early_output = False
    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) != 15 or fields[0] != "TRACE":
            continue
        reset = fields[2] == "0"
        if reset:
            if not was_reset:
                episode += 1
                accepted = 0
            was_reset = True
            continue
        was_reset = False
        if fields[3:5] == ["1", "1"]:
            accepted += 1
        if episode == 2 and any(fields[index] == "1" for index in (6, 9, 12)):
            observed_early_output = True
            assert accepted < 6
    assert observed_early_output
