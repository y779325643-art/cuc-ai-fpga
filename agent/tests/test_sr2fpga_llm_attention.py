"""Independent math, persistent state, static construction and actual HDL checks."""

from dataclasses import asdict
import json
import random

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.local_tools import resolve_executable
from sr2fpga_agent.pc.checker import check_design
from sr2fpga_agent.pc.emitter import BEHAVIOR_CONTRACT, build_structure, compose_behavior, write_project
from sr2fpga_agent.tasks.llm_attention import build_development_task, reference_design
from sr2fpga_agent.tasks.llm_attention.harness import (TESTBENCH_TOP, check_trace,
                                                    development_commands, render_testbench)
from sr2fpga_agent.tasks.llm_attention.oracle import (DecodeInput, DecodeOracle,
                                                   nearest_even, pack_vectors, unpack_vectors)
from sr2fpga_agent.tasks.llm_attention.reference import reference_behavior_bodies, render_reference_project
from sr2fpga_agent.tasks.llm_attention.task import EXP_LUT
from sr2fpga_agent.tool_runner import CommandRunner


def _build():
    task = build_development_task()
    checked = check_design(reference_design(), task["boundary"]["boundary"],
                           task["capability_profile"]["limits"], facts=task["facts"],
                           public_assets=task["public_assets"])
    bindings = {name: {"id": name, "sha256": "0" * 64}
                for name in ("requirements", "target_profile", "capability_profile")}
    return build_structure(checked, bindings=bindings)


def test_public_task_schemas_static_scope_and_actual_gqa_groups():
    task = build_development_task()
    registry = ContractRegistry()
    for key, value in (("development_public_boundary", task["boundary"]),
                       ("design_proposal_2_1", reference_design()),
                       ("pc21_development_target", task["target_profile"]),
                       ("pc21_development_capability", task["capability_profile"])):
        assert registry.load_schema(key).validate(value) == ()
    assert not {"oracle", "expected", "harness", "commands"} & task.keys()
    assert task["development_only"] is True
    assert task["facts"]["compute"]["value"]["query_heads"] == 4
    assert task["facts"]["compute"]["value"]["kv_heads"] == 2
    build = _build()
    assert len(build.units) == 1 and len(build.files) == 1
    unit = next(iter(build.units.values()))
    assert unit["module_id"] == "CachedDecodeAttention"
    assert all(port["width"] in (1, 18) for port in unit["ports"])
    assert len(build.build_plan_sha256) == 64


@pytest.mark.parametrize("n,d,expected", [(1,2,0),(3,2,2),(5,2,2),(-1,2,0),(-3,2,-2),(-5,2,-2),(-7,4,-2)])
def test_signed_rounding_examples(n, d, expected):
    assert nearest_even(n, d) == expected


def test_hand_golden_two_groups_persistent_cache_reset_and_capacity():
    commands = development_commands()
    oracle = DecodeOracle()
    assert oracle.decode(commands[0]) == (10,-10,5)*2 + (-30,20,11)*2
    assert oracle.decode(commands[1]) == (15,-2,1)*2 + (-12,4,21)*2
    assert oracle.valid_length == 2
    oracle.decode(commands[2])
    oracle.decode(commands[3])
    assert oracle.valid_length == 4
    with pytest.raises(ValueError, match="cache full"):
        oracle.decode(commands[4])
    oracle.reset()
    assert oracle.valid_length == 0
    assert oracle.decode(commands[4]) == (-80,60,7)*2 + (91,-44,-9)*2


def _cross_reference(history, query):
    def rounded(n, d):
        quotient, remainder = divmod(abs(n), d)
        quotient += int(2*remainder > d or 2*remainder == d and quotient % 2)
        return -quotient if n < 0 else quotient
    answer = []
    for h in range(4):
        indices = range((h // 2)*3, (h // 2 + 1)*3)
        scores = []
        for command in history:
            dot = sum(query[h*3 + d] * command.key[index] for d, index in enumerate(indices))
            scores.append(min(8, max(-8, rounded(37*dot, 1024))))
        weights = [EXP_LUT[max(scores)-score] for score in scores]
        for index in indices:
            answer.append(rounded(sum(weight*command.value[index] for weight, command in zip(weights, history)), sum(weights)))
    return tuple(answer)


def test_independent_random_math_includes_score_clipping_and_old_token_dependence():
    rng = random.Random(31951)
    for _ in range(16):
        oracle = DecodeOracle()
        history = []
        for _ in range(4):
            command = DecodeInput(tuple(rng.randrange(-128, 128) for _ in range(12)),
                                  tuple(rng.randrange(-128, 128) for _ in range(6)),
                                  tuple(rng.randrange(-128, 128) for _ in range(6)))
            history.append(command)
            assert oracle.decode(command) == _cross_reference(history, command.query)
    first, second = development_commands()[:2]
    full = DecodeOracle()
    full.decode(first)
    persistent = full.decode(second)
    assert persistent != DecodeOracle().decode(second)
    # Both groups have distinct public inputs; aliasing group one to zero changes answers.
    assert persistent[:6] != persistent[6:]


def test_pack_goldens_and_invalid_tail_fail_closed():
    assert pack_vectors((-128,127,-1,1,2,3),2) == (0x37F80,0x100FF,0x30201,0x10003)
    assert unpack_vectors((0x37F80,0x100FF,0x30201,0x10003),2) == (-128,127,-1,1,2,3)
    with pytest.raises(ValueError, match="invalid tail"):
        unpack_vectors((0x37F80,0x101FF),1)


def _single_command_trace(final_accept=40):
    command = development_commands()[0]
    expected = DecodeOracle().decode(command)
    lines = []
    cycle = 0
    def emit(name=None, beat=0, output=None):
        nonlocal cycle
        cycle += 1
        inputs = [(1,1,beat) if stream == name else (0,1,0) for stream in ("q","k","v")]
        signals = " ".join(f"{iv} {ir} {payload:05x}" for iv,ir,payload in inputs)
        lines.append(f"TRACE {cycle} 1 {signals} {int(output is not None)} 1 {output or 0:05x}")
    for name, values, heads in (("q",command.query,4),("k",command.key,2),("v",command.value,2)):
        for beat in pack_vectors(values,heads):
            emit(name,beat)
    beats = pack_vectors(expected,4)
    for beat in beats[:-1]:
        emit(output=beat)
    while cycle < final_accept-1:
        emit()
    emit(output=beats[-1])
    return "\n".join(lines)+f"\nTRACE_END {cycle}\n"


def test_trace_validates_values_completion_and_final_accept_deadline():
    assert check_trace(_single_command_trace(), expected_completed=1).output_beats == 8
    assert check_trace(_single_command_trace(257), expected_completed=1).completed_invocations == 1
    with pytest.raises(ValueError, match="bounded attention"):
        check_trace(_single_command_trace(258), expected_completed=1)
    with pytest.raises(ValueError, match="incomplete"):
        check_trace("TEST_PASS\n")
    # Corrupt the first offered output without depending on the particular hex golden.
    lines = _single_command_trace().splitlines()
    for index,line in enumerate(lines):
        fields = line.split()
        if len(fields) == 15 and fields[12] == "1":
            fields[14] = f"{int(fields[14],16)^1:05x}"
            lines[index] = " ".join(fields)
            break
    with pytest.raises(ValueError, match="output mismatch"):
        check_trace("\n".join(lines),expected_completed=1)


def _simulate(files, root, *, commands=None):
    if not resolve_executable("iverilog") or not resolve_executable("vvp"):
        pytest.skip("Icarus/vvp unavailable; mathematical checks do not establish HDL verification")
    for name, text in files.items():
        target = root/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding="utf-8")
    (root/"trusted_tb.sv").write_text(render_testbench(commands),encoding="utf-8")
    runner = CommandRunner()
    compilation = runner.run(["iverilog","-v","-g2012","-s",TESTBENCH_TOP,"-o","simulation.vvp",
                              *[name for name in files if name.endswith(".sv")],"trusted_tb.sv"],root,"compile")
    (root/"compile.json").write_text(json.dumps(asdict(compilation),indent=2),encoding="utf-8")
    assert compilation.status == "passed", asdict(compilation)
    simulation = runner.run(["vvp","simulation.vvp"],root,"simulate")
    (root/"simulation.json").write_text(json.dumps(asdict(simulation),indent=2),encoding="utf-8")
    assert simulation.status == "passed",asdict(simulation)
    result = check_trace(simulation.stdout)
    assert result.completed_invocations == 6 and result.output_beats == 48
    assert result.max_valid_cache_length == 4 and result.final_valid_cache_length == 2
    assert result.resets == 4 and result.cancelled_invocations == 2
    return result


def test_manual_reference_hdl_checks_persistence_gqa_stalls_and_resets(tmp_path):
    _simulate(render_reference_project(),tmp_path)


@pytest.mark.parametrize("bound", [-128, 127])
def test_reference_hdl_ratio_extremes_with_denominator_1024(bound, tmp_path):
    # Four equal-score tokens each have weight256. At the fourth decode:
    # den=1024, and AV is exactly -131072 or130048. The negative magnitude
    # must be held unsigned instead of overflowing a signed18 abs value.
    commands = tuple(DecodeInput((0,)*12, (0,)*6, (bound,)*6) for _ in range(6))
    _simulate(render_reference_project(),tmp_path,commands=commands)


def test_pc_emitted_reference_real_parser_and_hdl(tmp_path):
    if not resolve_executable("yosys"):
        pytest.skip("real Yosys required for the protected composition boundary")
    build = _build()
    bodies = reference_behavior_bodies()
    bundle = {"contract_version": BEHAVIOR_CONTRACT, "build_plan_sha256": build.build_plan_sha256,
              "units": {key: {"body": bodies[unit["module_id"]]} for key,unit in build.units.items()}}
    project = compose_behavior(build,bundle,scratch_root=tmp_path/"parser",
                               behavior_origin="hand_authored_development_control")
    project_root = write_project(project,tmp_path/"project")
    assert all(record["returncode"] == 0 for record in project.parser_evidence.values())
    _simulate(project.files,project_root)
