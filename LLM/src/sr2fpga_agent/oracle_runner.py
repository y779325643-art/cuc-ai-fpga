"""Execute evaluator-local oracle scenarios in isolated simulator processes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from LLM.src.sr2fpga_agent.log_parser import parse_test_fail_mismatches
from LLM.src.sr2fpga_agent.models import ToolResult
from LLM.src.sr2fpga_agent.oracles.bundle import load_oracle_bundle
from LLM.src.sr2fpga_agent.oracles.types import (
    OracleBundle,
    OracleRunEvidence,
    OracleScenarioManifest,
    OracleScenarioResult,
)
from LLM.src.sr2fpga_agent.tool_runner import CommandRunner


def run_oracle_scenarios(
    command_runner: CommandRunner,
    project_dir: Path,
    bundle: OracleBundle,
) -> tuple[OracleRunEvidence, ToolResult]:
    """Validate a bundle, run every scenario independently, and aggregate L2."""

    try:
        validated_bundle = load_oracle_bundle(bundle.root)
    except (OSError, ValueError) as exc:
        evidence = OracleRunEvidence(
            family_id=bundle.family_id,
            bundle_sha256=bundle.bundle_sha256,
            status="failed",
            failure_origin="oracle_environment_failure",
            failure_type=_oracle_failure_type(exc),
            scenario_results=(),
            diagnostics=(str(exc),),
        )
        return evidence, aggregate_oracle_tool_result(evidence)

    scenario_results = tuple(
        _run_scenario(command_runner, Path(project_dir), validated_bundle, scenario)
        for scenario in validated_bundle.scenarios
    )
    evidence = OracleRunEvidence.from_results(validated_bundle, scenario_results)
    return evidence, aggregate_oracle_tool_result(evidence)


def _run_scenario(
    command_runner: CommandRunner,
    project_dir: Path,
    bundle: OracleBundle,
    scenario: OracleScenarioManifest,
) -> OracleScenarioResult:
    command = [
        "vvp",
        "sim.out",
        f"+ORACLE_INPUT={(bundle.root / scenario.input_path).resolve()}",
        f"+ORACLE_EXPECTED={(bundle.root / scenario.expected_path).resolve()}",
        f"+ORACLE_SCENARIO_ID={scenario.scenario_id}",
        f"+ORACLE_SCENARIO_CLASS={scenario.scenario_class}",
        f"+ORACLE_TRANSACTION_COUNT={scenario.transaction_count}",
    ]
    raw_result = command_runner.run(command, cwd=project_dir, stage="sim_run")
    result, failure_origin, failure_type = validate_oracle_simulation_output(raw_result)
    mismatch_detail = tuple(
        parse_test_fail_mismatches(f"{result.stdout}\n{result.stderr}")
    )
    return OracleScenarioResult.from_tool_result(
        scenario,
        result,
        failure_origin=failure_origin,
        failure_type=failure_type,
        mismatch_detail=mismatch_detail,
    )


def validate_oracle_simulation_output(
    result: ToolResult,
) -> tuple[ToolResult, str | None, str | None]:
    """Normalize simulator markers while preserving failure provenance."""

    log_text = f"{result.stdout}\n{result.stderr}"
    markers = {
        line.strip()
        for line in log_text.splitlines()
        if line.strip() in {"TEST_PASS", "TEST_FAIL"}
    }
    if result.status == "missing_tool":
        return (
            _failed_result(result),
            "toolchain_environment_failure",
            "toolchain_environment_failure",
        )
    if result.status == "timeout":
        return _failed_result(result), "natural_model_failure", "testbench_timeout"
    if "TEST_FAIL" in markers:
        failure_type = "testbench_timeout" if "timeout" in log_text.lower() else "functional_mismatch"
        return _failed_result(result), "natural_model_failure", failure_type
    if result.status != "passed":
        return (
            _failed_result(result),
            "toolchain_environment_failure",
            "simulator_execution_failure",
        )
    if "TEST_PASS" not in markers:
        return (
            _failed_result(result, stderr_suffix="Simulation did not report TEST_PASS."),
            "natural_model_failure",
            "testbench_missing_pass_marker",
        )
    return result, None, None


def _failed_result(result: ToolResult, *, stderr_suffix: str = "") -> ToolResult:
    stderr = result.stderr
    if stderr_suffix:
        stderr = f"{stderr.rstrip()}\n{stderr_suffix}".lstrip()
    return ToolResult(
        stage="sim_run",
        command=list(result.command),
        status="failed",
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=stderr,
        duration_seconds=result.duration_seconds,
    )


def aggregate_oracle_tool_result(evidence: OracleRunEvidence) -> ToolResult:
    """Collapse scenario evidence into the existing aggregate ToolResult API."""

    scenario_results = evidence.scenario_results
    return ToolResult(
        stage="sim_run",
        command=["vvp", "sim.out", "<independent-oracle-scenarios>"],
        status=evidence.status,
        exit_code=0 if evidence.status == "passed" else 1,
        stdout="\n".join(
            f"[{result.scenario_id}] {result.stdout.rstrip()}" for result in scenario_results
        ).rstrip(),
        stderr="\n".join(
            [*evidence.diagnostics]
            + [
                f"[{result.scenario_id}] {result.stderr.rstrip()}"
                for result in scenario_results
                if result.stderr
            ]
        ).rstrip(),
        duration_seconds=sum(result.duration_seconds for result in scenario_results),
    )


def write_oracle_run_evidence(path: Path, evidence: OracleRunEvidence) -> None:
    """Write stable evaluator evidence outside the generated project."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(evidence.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def _oracle_failure_type(exc: Exception) -> str:
    text = str(exc).lower()
    if "hash mismatch" in text:
        return "oracle_hash_mismatch"
    if "missing oracle record file" in text:
        return "oracle_input_missing"
    return "oracle_bundle_invalid"
