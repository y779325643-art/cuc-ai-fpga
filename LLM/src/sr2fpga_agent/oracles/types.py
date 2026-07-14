"""Immutable data types for evaluator-local oracle bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from LLM.src.sr2fpga_agent.models import ToolResult


SCENARIO_CLASSES = frozenset(
    {"public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress"}
)


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

    @classmethod
    def from_results(
        cls,
        bundle: OracleBundle,
        results: tuple[OracleScenarioResult, ...],
    ) -> "OracleRunEvidence":
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
