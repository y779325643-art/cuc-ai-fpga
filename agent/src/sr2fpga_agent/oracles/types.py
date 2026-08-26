"""Immutable data types for evaluator-local oracle bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sr2fpga_agent.models import ToolResult


SCENARIO_CLASSES = frozenset(
    {"public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress"}
)
EXECUTION_FAILURE_ORIGINS = frozenset(
    {
        "natural_model_failure",
        "toolchain_environment_failure",
        "oracle_environment_failure",
    }
)
INFRASTRUCTURE_FAILURE_ORIGINS = frozenset(
    {"toolchain_environment_failure", "oracle_environment_failure"}
)


def _validate_execution_outcome(
    *,
    status: str,
    failure_origin: str | None,
    failure_type: str | None,
) -> None:
    if status not in {"passed", "failed"}:
        raise ValueError(f"unsupported oracle execution status: {status!r}")
    if status == "passed":
        if failure_origin is not None or failure_type is not None:
            raise ValueError("passed oracle execution cannot carry failure metadata")
        return
    if failure_origin not in EXECUTION_FAILURE_ORIGINS:
        raise ValueError(
            "failed oracle execution requires a registered failure_origin; "
            f"got {failure_origin!r}"
        )
    if not isinstance(failure_type, str) or not failure_type.strip():
        raise ValueError("failed oracle execution requires a non-empty failure_type")


@dataclass(frozen=True)
class OracleField:
    name: str
    msb: int
    lsb: int
    signed: bool


@dataclass(frozen=True)
class OracleScenarioSpec:
    scenario_id: str
    scenario_class: str
    seed: int
    input_record_width_bits: int
    expected_record_width_bits: int
    input_fields: tuple[OracleField, ...]
    expected_fields: tuple[OracleField, ...]
    input_records: tuple[int, ...]
    expected_records: tuple[int, ...]


@dataclass(frozen=True)
class OracleScenarioManifest:
    scenario_id: str
    scenario_class: str
    seed: int
    input_path: str
    expected_path: str
    transaction_count: int
    input_record_width_bits: int
    expected_record_width_bits: int
    input_fields: tuple[OracleField, ...]
    expected_fields: tuple[OracleField, ...]
    input_sha256: str
    expected_sha256: str


@dataclass(frozen=True)
class OracleBundle:
    root: Path
    family_id: str
    reference_model: str
    reference_version: str
    task_parameters: dict[str, object]
    scenarios: tuple[OracleScenarioManifest, ...]
    bundle_sha256: str
    manifest: dict[str, object]


@dataclass(frozen=True)
class OracleScenarioResult:
    scenario_id: str
    scenario_class: str
    status: str
    failure_origin: str | None
    failure_type: str | None
    command: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    mismatch_detail: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        _validate_execution_outcome(
            status=self.status,
            failure_origin=self.failure_origin,
            failure_type=self.failure_type,
        )

    @classmethod
    def from_tool_result(
        cls,
        scenario: OracleScenarioManifest,
        result: ToolResult,
        *,
        failure_origin: str | None = None,
        failure_type: str | None = None,
        mismatch_detail: tuple[dict[str, object], ...] = (),
    ) -> "OracleScenarioResult":
        return cls(
            scenario_id=scenario.scenario_id,
            scenario_class=scenario.scenario_class,
            status=result.status,
            failure_origin=failure_origin,
            failure_type=failure_type,
            command=tuple(result.command),
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=result.duration_seconds,
            mismatch_detail=mismatch_detail,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_class": self.scenario_class,
            "status": self.status,
            "failure_origin": self.failure_origin,
            "failure_type": self.failure_type,
            "command": list(self.command),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "mismatch_detail": [dict(item) for item in self.mismatch_detail],
        }


@dataclass(frozen=True)
class OracleRunEvidence:
    family_id: str
    bundle_sha256: str
    status: str
    failure_origin: str | None
    failure_type: str | None
    scenario_results: tuple[OracleScenarioResult, ...]
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_execution_outcome(
            status=self.status,
            failure_origin=self.failure_origin,
            failure_type=self.failure_type,
        )

    @classmethod
    def from_results(
        cls,
        bundle: OracleBundle,
        results: tuple[OracleScenarioResult, ...],
    ) -> "OracleRunEvidence":
        present_classes = {result.scenario_class for result in results}
        missing_classes = sorted(SCENARIO_CLASSES - present_classes)
        if missing_classes:
            return cls(
                family_id=bundle.family_id,
                bundle_sha256=bundle.bundle_sha256,
                status="failed",
                failure_origin="oracle_environment_failure",
                failure_type="oracle_scenario_class_missing",
                scenario_results=results,
                diagnostics=(
                    "missing required oracle scenario classes: "
                    + ", ".join(missing_classes),
                ),
            )
        failed = tuple(result for result in results if result.status != "passed")
        failure = _primary_failure(failed)
        return cls(
            family_id=bundle.family_id,
            bundle_sha256=bundle.bundle_sha256,
            status="passed" if not failed else "failed",
            failure_origin=failure.failure_origin if failure else None,
            failure_type=failure.failure_type if failure else None,
            scenario_results=results,
        )

    def scenario_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for result in self.scenario_results:
            counts[result.scenario_class] = counts.get(result.scenario_class, 0) + 1
        return counts

    def class_status(self, scenario_class: str) -> str:
        results = tuple(
            result for result in self.scenario_results if result.scenario_class == scenario_class
        )
        if not results:
            return "not_run"
        return "pass" if all(result.status == "passed" for result in results) else "fail"

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": "development-oracle-run-evidence-v1",
            "evaluation_scope": "development_independent_oracle",
            "family_id": self.family_id,
            "bundle_sha256": self.bundle_sha256,
            "status": self.status,
            "failure_origin": self.failure_origin,
            "failure_type": self.failure_type,
            "scenario_counts": self.scenario_counts(),
            "class_status": {
                scenario_class: self.class_status(scenario_class)
                for scenario_class in sorted(SCENARIO_CLASSES)
            },
            "scenario_results": [result.to_dict() for result in self.scenario_results],
            "diagnostics": list(self.diagnostics),
            "pass_credit_authority": False,
            "official_outcome": False,
        }


def _primary_failure(
    results: tuple[OracleScenarioResult, ...],
) -> OracleScenarioResult | None:
    precedence = {
        "oracle_environment_failure": 0,
        "toolchain_environment_failure": 1,
        "natural_model_failure": 2,
    }
    return min(
        results,
        key=lambda result: precedence.get(result.failure_origin or "", 3),
        default=None,
    )
