import json
from pathlib import Path

from LLM.src.sr2fpga_agent.models import ToolResult
from LLM.src.sr2fpga_agent.oracle_runner import (
    run_oracle_scenarios,
    write_oracle_run_evidence,
)
from LLM.src.sr2fpga_agent.oracles import OracleField, OracleScenarioSpec, write_oracle_bundle


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
        self.calls.append(
            {
                "command": list(command),
                "cwd": Path(cwd),
                "stage": stage,
                "timeout_seconds": timeout_seconds,
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


def _bundle(tmp_path):
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
        for index, scenario_class in enumerate(SCENARIO_CLASSES)
    )
    return write_oracle_bundle(
        root=tmp_path / "oracle",
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
    for call, scenario in zip(runner.calls, bundle.scenarios):
        command = call["command"]
        assert f"+ORACLE_INPUT={(bundle.root / scenario.input_path).resolve()}" in command
        assert f"+ORACLE_EXPECTED={(bundle.root / scenario.expected_path).resolve()}" in command
        assert f"+ORACLE_SCENARIO_ID={scenario.scenario_id}" in command
        assert f"+ORACLE_SCENARIO_CLASS={scenario.scenario_class}" in command
        assert f"+ORACLE_TRANSACTION_COUNT={scenario.transaction_count}" in command
    assert tool_result.status == "passed"
    assert evidence.status == "passed"
    assert evidence.failure_origin is None
    assert evidence.scenario_counts() == {scenario_class: 1 for scenario_class in SCENARIO_CLASSES}
    assert all(evidence.class_status(scenario_class) == "pass" for scenario_class in SCENARIO_CLASSES)


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
                    "TEST_FAIL expected=0a actual=09\n"
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


def test_class_status_requires_a_present_scenario(tmp_path):
    bundle = _bundle(tmp_path)
    public_only = write_oracle_bundle(
        root=tmp_path / "public_only",
        family_id=bundle.family_id,
        reference_model=bundle.reference_model,
        reference_version=bundle.reference_version,
        task_parameters=bundle.task_parameters,
        scenarios=(
            OracleScenarioSpec(
                scenario_id="public_smoke_only",
                scenario_class="public_smoke",
                seed=1,
                input_record_width_bits=8,
                expected_record_width_bits=8,
                input_fields=(OracleField("sample", 7, 0, False),),
                expected_fields=(OracleField("result", 7, 0, False),),
                input_records=(1,),
                expected_records=(1,),
            ),
        ),
    )

    evidence, tool_result = run_oracle_scenarios(FakeCommandRunner(), tmp_path, public_only)

    assert tool_result.status == "passed"
    assert evidence.class_status("public_smoke") == "pass"
    assert evidence.class_status("stress") == "not_run"


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
