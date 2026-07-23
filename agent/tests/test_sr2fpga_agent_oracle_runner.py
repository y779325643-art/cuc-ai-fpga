import json
from pathlib import Path

import pytest

import sr2fpga_agent.oracle_runner as oracle_runner_module
from sr2fpga_agent.models import ToolResult
from sr2fpga_agent.oracle_runner import (
    run_oracle_scenarios,
    write_oracle_run_evidence,
)
from sr2fpga_agent.oracles import OracleField, OracleScenarioSpec, write_oracle_bundle


SCENARIO_CLASSES = (
    "public_smoke",
    "hidden_deterministic",
    "randomized_fixed_seed",
    "stress",
)


class FakeCommandRunner:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []

    def run(self, command, cwd, stage, timeout_seconds=30):
        staged_vectors = {}
        for prefix in ("+ORACLE_INPUT=", "+ORACLE_EXPECTED="):
            value = next(
                (
                    item.removeprefix(prefix)
                    for item in command
                    if item.startswith(prefix)
                ),
                None,
            )
            if value is not None:
                staged_path = Path(cwd) / value
                staged_vectors[prefix] = {
                    "value": value,
                    "exists": staged_path.is_file(),
                    "content": staged_path.read_bytes()
                    if staged_path.is_file()
                    else None,
                }
        self.calls.append(
            {
                "command": list(command),
                "cwd": Path(cwd),
                "stage": stage,
                "timeout_seconds": timeout_seconds,
                "staged_vectors": staged_vectors,
            }
        )
        if self.results:
            return self.results.pop(0)
        return _tool_result(stdout="TEST_PASS\n")


def _tool_result(*, status="passed", stdout="", stderr="", exit_code=0):
    return ToolResult(
        stage="sim_run",
        command=["vvp", "sim.out"],
        status=status,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=0.01,
    )


def _bundle(tmp_path, scenario_classes=SCENARIO_CLASSES, *, root_name="oracle"):
    scenarios = tuple(
        OracleScenarioSpec(
            scenario_id=f"{scenario_class}_001",
            scenario_class=scenario_class,
            seed=100 + index,
            input_record_width_bits=8,
            expected_record_width_bits=8,
            input_fields=(OracleField("sample", 7, 0, False),),
            expected_fields=(OracleField("result", 7, 0, False),),
            input_records=(index,),
            expected_records=(index,),
        )
        for index, scenario_class in enumerate(scenario_classes)
    )
    return write_oracle_bundle(
        root=tmp_path / root_name,
        family_id="fir_filter",
        reference_model="numeric.fir_filter",
        reference_version="1",
        task_parameters={"width": 8},
        scenarios=scenarios,
    )


def test_runner_invokes_vvp_once_per_scenario_and_aggregates_all_pass(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    evidence, tool_result = run_oracle_scenarios(runner, project_dir, bundle)

    assert len(runner.calls) == 4
    assert all(call["command"][:2] == ["vvp", "sim.out"] for call in runner.calls)
    assert all(call["cwd"] == project_dir for call in runner.calls)
    assert all(call["stage"] == "sim_run" for call in runner.calls)
    for index, (call, scenario) in enumerate(zip(runner.calls, bundle.scenarios)):
        command = call["command"]
        input_argument = next(
            item for item in command if item.startswith("+ORACLE_INPUT=")
        )
        expected_argument = next(
            item for item in command if item.startswith("+ORACLE_EXPECTED=")
        )
        input_value = input_argument.removeprefix("+ORACLE_INPUT=")
        expected_value = expected_argument.removeprefix("+ORACLE_EXPECTED=")
        assert Path(input_value).parent.name.startswith("sr2fpga_oracle_")
        assert Path(input_value).name == f"{index:02d}.input.memh"
        assert Path(expected_value).parent.name.startswith("sr2fpga_oracle_")
        assert Path(expected_value).name == f"{index:02d}.expected.memh"
        assert call["staged_vectors"]["+ORACLE_INPUT="]["exists"]
        assert call["staged_vectors"]["+ORACLE_EXPECTED="]["exists"]
        assert call["staged_vectors"]["+ORACLE_INPUT="]["content"] == (
            bundle.root / scenario.input_path
        ).read_bytes()
        assert call["staged_vectors"]["+ORACLE_EXPECTED="]["content"] == (
            bundle.root / scenario.expected_path
        ).read_bytes()
        assert f"+ORACLE_SCENARIO_ID={scenario.scenario_id}" in command
        assert f"+ORACLE_SCENARIO_CLASS={scenario.scenario_class}" in command
        assert f"+ORACLE_TRANSACTION_COUNT={scenario.transaction_count}" in command
    assert tool_result.status == "passed"
    assert evidence.status == "passed"
    assert evidence.failure_origin is None
    assert evidence.scenario_counts() == {scenario_class: 1 for scenario_class in SCENARIO_CLASSES}
    assert all(evidence.class_status(scenario_class) == "pass" for scenario_class in SCENARIO_CLASSES)


def test_runner_keeps_oracle_plusargs_relative_in_deep_workspaces(tmp_path):
    deep_root = tmp_path.joinpath(*(["nested_workspace"] * 6))
    bundle = _bundle(deep_root)
    runner = FakeCommandRunner()
    project_dir = deep_root / "project"
    project_dir.mkdir()

    run_oracle_scenarios(runner, project_dir, bundle)

    for call in runner.calls:
        for prefix in ("+ORACLE_INPUT=", "+ORACLE_EXPECTED="):
            value = next(
                item.removeprefix(prefix)
                for item in call["command"]
                if item.startswith(prefix)
            )
            assert Path(value).is_absolute()
            assert "\\" not in value
            assert len(value) < 180


def test_one_dut_mismatch_fails_aggregate_and_keeps_structured_detail(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner(
        [
            _tool_result(stdout="TEST_PASS\n"),
            _tool_result(
                status="failed",
                exit_code=1,
                stdout=(
                    'SR2FPGA_MISMATCH {"scenario_id":"hidden_deterministic_001",'
                    '"class":"hidden_deterministic","item_index":2,'
                    '"expected":"0a","actual":"09"}\n'
                    "TEST_FAIL\n"
                ),
            ),
            _tool_result(stdout="TEST_PASS\n"),
            _tool_result(stdout="TEST_PASS\n"),
        ]
    )

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert tool_result.status == "failed"
    assert evidence.status == "failed"
    assert evidence.failure_origin == "natural_model_failure"
    assert evidence.failure_type == "functional_mismatch"
    assert evidence.class_status("hidden_deterministic") == "fail"
    mismatch = evidence.scenario_results[1].mismatch_detail
    assert mismatch == (
        {
            "scenario_id": "hidden_deterministic_001",
            "class": "hidden_deterministic",
            "item_index": 2,
            "expected": "0a",
            "actual": "09",
        },
    )


def test_process_timeout_is_a_model_failure_and_does_not_stop_later_scenarios(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner(
        [
            _tool_result(status="timeout", exit_code=None, stderr="timed out"),
            _tool_result(stdout="TEST_PASS\n"),
            _tool_result(stdout="TEST_PASS\n"),
            _tool_result(stdout="TEST_PASS\n"),
        ]
    )

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert len(runner.calls) == 4
    assert tool_result.status == "failed"
    assert evidence.failure_origin == "natural_model_failure"
    assert evidence.failure_type == "testbench_timeout"


def test_invalid_bundle_hash_is_non_model_failure_without_invoking_simulator(tmp_path):
    bundle = _bundle(tmp_path)
    input_path = bundle.root / bundle.scenarios[0].input_path
    input_path.write_text("ff\n", encoding="ascii")
    runner = FakeCommandRunner()

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert runner.calls == []
    assert tool_result.status == "failed"
    assert evidence.status == "failed"
    assert evidence.failure_origin == "oracle_environment_failure"
    assert evidence.failure_type == "oracle_hash_mismatch"


def test_missing_simulator_is_toolchain_environment_failure(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner(
        [_tool_result(status="missing_tool", exit_code=None, stderr="Missing executable: vvp") for _ in range(4)]
    )

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert tool_result.status == "failed"
    assert evidence.failure_origin == "toolchain_environment_failure"
    assert evidence.failure_type == "toolchain_environment_failure"
    assert all(result.failure_origin == "toolchain_environment_failure" for result in evidence.scenario_results)


@pytest.mark.parametrize("missing_class", SCENARIO_CLASSES)
def test_each_missing_scenario_class_is_an_oracle_qualification_failure(
    tmp_path,
    missing_class,
):
    present_classes = tuple(item for item in SCENARIO_CLASSES if item != missing_class)
    bundle = _bundle(tmp_path, present_classes)

    evidence, tool_result = run_oracle_scenarios(FakeCommandRunner(), tmp_path, bundle)

    assert tool_result.status == "failed"
    assert evidence.status == "failed"
    assert evidence.failure_origin == "oracle_environment_failure"
    assert evidence.failure_type == "oracle_scenario_class_missing"
    assert evidence.class_status(missing_class) == "not_run"
    assert missing_class in evidence.diagnostics[0]


@pytest.mark.parametrize(
    "stdout",
    (
        "NOT_TEST_PASS\n",
        "Narrative text says TEST_PASS but is not a marker.\n",
        "prefix TEST_PASS\n",
    ),
)
def test_pass_marker_must_be_an_independent_line(tmp_path, stdout):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner([_tool_result(stdout=stdout) for _ in range(4)])

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert tool_result.status == "failed"
    assert evidence.failure_origin == "natural_model_failure"
    assert evidence.failure_type == "testbench_missing_pass_marker"


def test_strict_fail_marker_takes_priority_over_strict_pass_marker(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner(
        [_tool_result(stdout="TEST_PASS\nTEST_FAIL\n")]
        + [_tool_result(stdout="TEST_PASS\n") for _ in range(3)]
    )

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert tool_result.status == "failed"
    assert evidence.failure_origin == "natural_model_failure"
    assert evidence.failure_type == "functional_mismatch"


def test_oracle_vector_read_failure_takes_priority_over_test_pass(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner(
        [
            _tool_result(
                stdout=(
                    "ERROR: sim/tb_top.v:104: $readmemh: "
                    "Unable to open missing.memh for reading.\n"
                    "TEST_PASS\n"
                )
            )
        ]
        + [_tool_result(stdout="TEST_PASS\n") for _ in range(3)]
    )

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert tool_result.status == "failed"
    assert evidence.status == "failed"
    assert evidence.failure_origin == "oracle_environment_failure"
    assert evidence.failure_type == "oracle_vector_read_failure"
    assert evidence.scenario_results[0].failure_origin == (
        "oracle_environment_failure"
    )


def test_fail_marker_with_details_takes_priority_and_nonzero_is_model_failure(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner(
        [
            _tool_result(
                status="failed",
                exit_code=1,
                stdout="TEST_PASS\nTEST_FAIL expected=1 actual=0\n",
            )
        ]
        + [_tool_result(stdout="TEST_PASS\n") for _ in range(3)]
    )

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert tool_result.status == "failed"
    assert evidence.failure_origin == "natural_model_failure"
    assert evidence.failure_type == "functional_mismatch"
    assert evidence.scenario_results[0].mismatch_detail == (
        {"expected": "1", "actual": "0"},
    )


def test_not_test_fail_is_not_a_failure_marker(tmp_path):
    bundle = _bundle(tmp_path)
    runner = FakeCommandRunner(
        [_tool_result(stdout="NOT_TEST_FAIL expected=1 actual=0\nTEST_PASS\n") for _ in range(4)]
    )

    evidence, tool_result = run_oracle_scenarios(runner, tmp_path, bundle)

    assert tool_result.status == "passed"
    assert evidence.status == "passed"


def test_write_oracle_run_evidence_uses_stable_json(tmp_path):
    bundle = _bundle(tmp_path)
    evidence, _ = run_oracle_scenarios(FakeCommandRunner(), tmp_path, bundle)
    target = tmp_path / "eval" / "oracle_run.json"

    write_oracle_run_evidence(target, evidence)

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["family_id"] == "fir_filter"
    assert payload["bundle_sha256"] == bundle.bundle_sha256
    assert payload["status"] == "passed"
    assert len(payload["scenario_results"]) == 4


def test_write_oracle_run_evidence_is_byte_stable_across_rewrites(tmp_path):
    bundle = _bundle(tmp_path)
    evidence, _ = run_oracle_scenarios(FakeCommandRunner(), tmp_path, bundle)
    target = tmp_path / "eval" / "oracle_run.json"

    write_oracle_run_evidence(target, evidence)
    first = target.read_bytes()
    write_oracle_run_evidence(target, evidence)

    assert target.read_bytes() == first


def test_atomic_evidence_replace_failure_preserves_previous_file(tmp_path, monkeypatch):
    bundle = _bundle(tmp_path)
    evidence, _ = run_oracle_scenarios(FakeCommandRunner(), tmp_path, bundle)
    target = tmp_path / "eval" / "oracle_run.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"previous evidence\n")

    def fail_replace(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr(oracle_runner_module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        write_oracle_run_evidence(target, evidence)

    assert target.read_bytes() == b"previous evidence\n"
    assert list(target.parent.glob(f".{target.name}.*.tmp")) == []
