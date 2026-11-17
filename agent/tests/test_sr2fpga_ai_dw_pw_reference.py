"""Task math, public boundary, byte packing and trusted-harness regressions."""

from __future__ import annotations

import random
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.tasks.ai_dw_pw import build_development_task, reference_design
from sr2fpga_agent.tasks.ai_dw_pw.harness import check_trace, development_frames, render_testbench
from sr2fpga_agent.tasks.ai_dw_pw.oracle import evaluate, nearest_even, pack_tensor, unpack_tensor
from sr2fpga_agent.tasks.ai_dw_pw.reference import render_reference_project
from sr2fpga_agent.tasks.ai_dw_pw.task import DW_WEIGHTS, DW_BIAS, PW_WEIGHTS, PW_BIAS, OUTPUT_ZEROS, OUTPUT_DENOMINATORS
from sr2fpga_agent.tool_runner import CommandRunner
from sr2fpga_agent.local_tools import resolve_executable


def cross_reference(values):
    """Distinct patch/dot-product implementation and signed divmod rounding."""
    def rounded(x, d):
        q, r = divmod(abs(x), d)
        if 2*r > d or 2*r == d and q % 2:
            q += 1
        return q if x >= 0 else -q
    result = []
    for pixel in range(20):
        h, w = divmod(pixel, 5)
        mids = []
        for channel in range(3):
            patch = []
            for dy, dx in ((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                y, x = h+dy, w+dx
                patch.append(values[(y*5+x)*3+channel]+3 if 0 <= y < 4 and 0 <= x < 5 else 0)
            kernel = [x for row in DW_WEIGHTS[channel] for x in row]
            acc = sum(a*b for a, b in zip(patch, kernel)) + DW_BIAS[channel]
            mids.append(max(2, min(127, max(-128, rounded(acc, 2)+2))))
        for channel in range(5):
            acc = sum(a*(b-2) for a, b in zip(PW_WEIGHTS[channel], mids)) + PW_BIAS[channel]
            result.append(min(127, max(-128, rounded(acc, OUTPUT_DENOMINATORS[channel])+OUTPUT_ZEROS[channel])))
    return tuple(result)


def test_public_task_boundary_and_manual_design_are_schema_valid():
    task = build_development_task()
    registry = ContractRegistry()
    assert not registry.load_schema("development_public_boundary").validate(task["boundary"])
    assert not registry.load_schema("design_proposal_2_1").validate(reference_design())
    assert task["development_only"] is True
    assert set(task["public_assets"]) == {"dw_pw_weights"}
    assert not {"oracle", "frames", "expected", "harness"} & set(task)


@pytest.mark.parametrize("value,divisor,expected", [(1,2,0),(3,2,2),(5,2,2),(-1,2,0),(-3,2,-2),(-5,2,-2),(7,4,2),(-7,4,-2)])
def test_signed_nearest_even_hand_values(value, divisor, expected):
    assert nearest_even(value, divisor) == expected


def test_hand_golden_padding_zero_point_and_pack_examples():
    # All raw -3 means mathematical zero, including padding. Bias alone gives
    # centered intermediates [0,2,0], PW sums [-11,7,5,-3,15].
    assert evaluate((-3,)*60) == (-8, 8, -7, 2, 0)*20
    assert pack_tensor((-128,127,-1),3) == (0x37F80,0x100FF)
    assert unpack_tensor((0x37F80,0x100FF),3) == (-128,127,-1)
    assert pack_tensor((-8,8,-7,2,0),5) == (0x308F8,0x302F9,0x10000)
    assert evaluate((0,)*60) != evaluate((-3,)*60)
    with pytest.raises(ValueError,match="invalid mask"):
        unpack_tensor((0x37F80,0x101FF),3)


def test_nonzero_impulse_hand_golden_kernel_axis_and_per_channel_scales():
    values = [-3]*60
    values[0] = 5  # At (h0,w0,c0), centered8 times DW center weight3.
    # DW c0 accumulator19 => nearest_even(9.5)+2=12, centered10.
    # Other channels stay centered2,0. PW sums are -1,-23,25,7,-5.
    assert evaluate(values)[:5] == (-5,4,3,5,-3)
    # The adjacent horizontal pixel sees kernel center-left weight0.
    assert evaluate(values)[5:10] == (-8,8,-7,2,0)


def test_distinct_math_crosscheck_and_accumulator_bounds():
    rng = random.Random(913)
    frames = list(development_frames()) + [tuple(rng.randrange(-128,128) for _ in range(60)) for _ in range(20)]
    for values in frames:
        assert evaluate(values) == cross_reference(values)
    # Worst centered input magnitude is131; intermediate ReLU gives0..125.
    for kernel, bias in zip(DW_WEIGHTS,DW_BIAS):
        assert 131*sum(abs(x) for row in kernel for x in row)+abs(bias) < 2**31
    for weights, bias in zip(PW_WEIGHTS,PW_BIAS):
        assert 125*sum(abs(x) for x in weights)+abs(bias) < 2**31


def test_trace_rejects_fake_pass_and_incomplete_schedules():
    with pytest.raises(ValueError,match="incomplete"):
        check_trace("TEST_PASS\n")
    with pytest.raises(ValueError,match="unexpected"):
        check_trace("TRACE 1 1 0 1 00000 1 1 10000\nTRACE_END 1\n")
    with pytest.raises(ValueError,match="noncontiguous"):
        check_trace("TRACE 2 1 0 1 00000 0 1 00000\nTRACE_END 2\n")
    with pytest.raises(ValueError,match="persisted after a reset edge"):
        check_trace("TRACE 1 0 0 x 00000 x 0 xxxxx\nTRACE 2 0 0 1 00000 1 0 10000\nTRACE_END 2\n")


def test_idle_unknown_payloads_are_legal_but_valid_unknown_payload_is_rejected():
    trace = "TRACE 1 1 0 1 xxxxx 0 1 xxxxx\nTRACE_END 1\n"
    assert check_trace(trace, expected_completed=0).completed_invocations == 0
    with pytest.raises(ValueError, match="unknown or invalid signal"):
        check_trace("TRACE 1 1 1 1 xxxxx 0 1 xxxxx\nTRACE_END 1\n", expected_completed=0)


def test_manual_control_hdl_end_to_end(tmp_path: Path):
    if not resolve_executable("iverilog") or not resolve_executable("vvp"):
        pytest.skip("Icarus/vvp unavailable; math-only tests do not establish HDL qualification")
    sources = render_reference_project()
    sources["trusted_dw_pw_tb.sv"] = render_testbench()
    for name, source in sources.items():
        (tmp_path/name).write_text(source, encoding="utf-8")
    runner = CommandRunner()
    # Verbose logs preserve backend diagnostics on this Windows toolchain.
    # Driver access violations remain failures; no retries or skip-on-failure.
    compile_result = runner.run(["iverilog","-v","-g2012","-s","trusted_dw_pw_tb","-o","simulation.vvp",*sources],tmp_path,"compile")
    (tmp_path/"compile.json").write_text(json.dumps(asdict(compile_result),indent=2),encoding="utf-8")
    assert compile_result.status == "passed", asdict(compile_result)
    simulation = runner.run(["vvp","simulation.vvp"],tmp_path,"simulate")
    (tmp_path/"simulation.json").write_text(json.dumps(asdict(simulation),indent=2),encoding="utf-8")
    assert simulation.status == "passed", simulation.stderr
    result = check_trace(simulation.stdout)
    assert result.completed_invocations == 3
    assert result.resets == 3 and result.cancelled_invocations == 2
    assert result.output_beats == 180
    # Real trace corruption must fail even if simulator and candidate say PASS.
    lines = simulation.stdout.splitlines()
    for i, line in enumerate(lines):
        fields = line.split()
        if len(fields) == 9 and fields[0] == "TRACE" and fields[6] == "1" and fields[7] == "1" and fields[2] == "1":
            fields[8] = f"{int(fields[8],16)^1:05x}"
            lines[i] = " ".join(fields)
            break
    with pytest.raises(ValueError,match="output mismatch"):
        check_trace("\n".join(lines)+"\nTEST_PASS\n")
