"""Reconcile a development-only excluded M0-M5 full-pack smoke."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from sr2fpga_agent.artifact_store import ArtifactIntegrityError, ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import COST_AXES
from sr2fpga_agent.episode_outcome import (
    EpisodeOutcomeRecord,
    reconcile_development_episode_outcome,
    reconcile_excluded_full_pack_outcomes,
)
from sr2fpga_agent.method_adapters import (
    MethodArtifactGateway,
    ProjectCandidateEmission,
)
from sr2fpga_agent.method_contract import MethodConditionId
from sr2fpga_agent.measurement_freeze import freeze_fingerprint
from sr2fpga_agent.paired_block import load_development_paired_block
from sr2fpga_agent.paired_cost_views import (
    MethodCostSource,
    reconcile_development_paired_block_costs,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_METHODS = tuple(condition.value for condition in MethodConditionId)
_SCENARIOS = {
    "success",
    "h_repair",
    "project_repair",
    "non_ready",
    "hidden_fail",
    "infrastructure_not_run",
}


@dataclass(frozen=True)
class FullPackMethodRecord:
    method_condition: str
    analysis_population: str
    pack_sha256: str
    public_projection_sha256: str
    candidate_artifact_key: str
    candidate_artifact_sha256: str
    project_package_sha256: str
    skeleton_artifact_sha256: str | None = None
    planning_kind: str | None = None
    planning_artifact_sha256: str | None = None
    h_status: str = "not_applicable"
    skeleton_mode: str = "none"


@dataclass(frozen=True)
class FullPackScenarioRecord:
    scenario_id: str
    scenario_kind: str
    analysis_population: str
    public_projection_sha256: str
    method_condition: str | None
    status: str
    facts: Mapping[str, Any]


@dataclass(frozen=True)
class FullPackRunnerArtifactRecord:
    method_condition: str
    trajectory_ref: ArtifactRef
    paired_block_ref: ArtifactRef | None = None


class FullPackReconciliationError(ValueError):
    pass


def reconcile_excluded_full_pack(
    store: ArtifactStore,
    *,
    smoke_id: str,
    methods: Iterable[FullPackMethodRecord],
    scenarios: Iterable[FullPackScenarioRecord],
) -> tuple[dict[str, Any], ArtifactRef]:
    """Validate and persist one non-official, excluded full-pack report."""

    method_records = tuple(methods)
    scenario_records = tuple(scenarios)
    _validate_methods(method_records)
    projection = method_records[0].public_projection_sha256
    _validate_scenarios(scenario_records, projection)
    report = {
        "contract_version": "full-pack-smoke-report-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "smoke_id": smoke_id,
        "analysis_population": "excluded",
        "registered_evidence_contract": True,
        "g3_accepted": False,
        "g4b_authorized": False,
        "official_outcome": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "public_projection_sha256": projection,
        "method_records": [asdict(record) for record in method_records],
        "scenario_records": [
            {**asdict(record), "facts": dict(record.facts)}
            for record in scenario_records
        ],
        "reconciliation": {
            "method_set": list(_METHODS),
            "same_public_projection": True,
            "m0_m1_initial_project_matched": True,
            "m3_m4_system_his_matched": True,
            "m3_m4_candidate_artifacts_separate": True,
            "m4_m5_skeleton_project_matched": True,
            "required_scenarios": sorted(_SCENARIOS),
            "all_required_scenarios_present": True,
            "full_axis_costs_reconciled": False,
            "blocking_gaps": [
                "full_axis_event_derived_cost_reconciliation",
                "runner_owned_public_terminal_hidden_pipeline",
            ],
        },
    }
    reference = store.put_validated_json(
        f"full-pack-smokes/{smoke_id}/report",
        report,
        contract_key="full_pack_smoke_report",
    )
    return report, reference


def reconcile_full_pack_runner_artifacts(
    store: ArtifactStore,
    *,
    smoke_id: str,
    source_smoke_report_ref: ArtifactRef,
    runner_artifacts: Iterable[FullPackRunnerArtifactRecord],
) -> tuple[dict[str, Any], ArtifactRef]:
    """Rebuild M0-M5 Runner lineage without upgrading the v1 smoke report."""

    registry = ContractRegistry()
    source_report = _read_registered_json(
        store,
        source_smoke_report_ref,
        registry=registry,
        contract_key="full_pack_smoke_report",
        label="source full-pack smoke report",
    )
    if source_report["smoke_id"] != smoke_id:
        raise FullPackReconciliationError("runner reconciliation smoke ID mismatch")
    if source_report["analysis_population"] != "excluded":
        raise FullPackReconciliationError("runner reconciliation source must be excluded")

    records = tuple(runner_artifacts)
    by_method = {record.method_condition: record for record in records}
    if len(records) != len(_METHODS) or set(by_method) != set(_METHODS):
        raise FullPackReconciliationError(
            "runner reconciliation must contain exactly one M0-M5 trajectory"
        )

    trajectory_contract = registry.load_schema("trajectory_v2")
    cost_contract = registry.load_schema("cost_summary")
    method_records: list[dict[str, Any]] = []
    hidden_count = 0
    projection = source_report["public_projection_sha256"]
    paired_refs = [record.paired_block_ref for record in records]
    paired_block_ref = None
    paired_block = None
    if any(reference is not None for reference in paired_refs):
        if any(reference is None for reference in paired_refs):
            raise FullPackReconciliationError(
                "runner reconciliation has incomplete paired-block references"
            )
        unique_refs = {reference for reference in paired_refs if reference is not None}
        if len(unique_refs) != 1:
            raise FullPackReconciliationError(
                "runner reconciliation paired-block references do not match"
            )
        paired_block_ref = next(iter(unique_refs))
        try:
            paired_block = load_development_paired_block(store, paired_block_ref)
        except (ArtifactIntegrityError, ValueError) as exc:
            raise FullPackReconciliationError(
                "runner reconciliation paired-block reference is invalid"
            ) from exc
        actual_order = tuple(record.method_condition for record in records)
        if actual_order != tuple(paired_block["method_order"]):
            raise FullPackReconciliationError(
                "runner execution order does not match paired-block method order"
            )
        if paired_block["public_projection_sha256"] != projection:
            raise FullPackReconciliationError(
                "runner paired block does not match the smoke public projection"
            )
    seen_episodes: set[str] = set()
    for method in _METHODS:
        record = by_method[method]
        trajectory = _read_and_validate(
            store,
            record.trajectory_ref,
            contract=trajectory_contract,
            label=f"{method} trajectory",
        )
        if trajectory["method_condition"] != method:
            raise FullPackReconciliationError(f"{method} trajectory method mismatch")
        episode_id = trajectory["episode_id"]
        if episode_id in seen_episodes:
            raise FullPackReconciliationError("runner trajectories must use distinct episodes")
        seen_episodes.add(episode_id)
        if trajectory["lineage_complete"] is not True:
            raise FullPackReconciliationError(f"{method} trajectory lineage is incomplete")
        terminal_ref = trajectory["terminal_candidate_ref"]
        if terminal_ref is None:
            raise FullPackReconciliationError(f"{method} terminal candidate is missing")
        terminal = _read_registered_json(
            store,
            ArtifactRef(**terminal_ref),
            registry=registry,
            contract_key="terminal_candidate",
            label=f"{method} terminal candidate",
        )
        if (
            terminal["episode_id"],
            terminal["method_condition_id"],
        ) != (episode_id, method):
            raise FullPackReconciliationError(f"{method} terminal identity mismatch")

        input_hashes = {
            value
            for attempt in trajectory["attempts"]
            for value in attempt["input_artifact_hashes"]
        }
        if projection not in input_hashes:
            raise FullPackReconciliationError(
                f"{method} trajectory is not bound to the smoke public projection"
            )
        if paired_block_ref is not None and any(
            paired_block_ref.sha256 not in attempt["input_artifact_hashes"]
            for attempt in trajectory["attempts"]
        ):
            raise FullPackReconciliationError(
                f"{method} trajectory attempt is not bound to the paired block"
            )
        summary_refs = [
            ArtifactRef(**attempt["cost_summary_ref"])
            for attempt in trajectory["attempts"]
        ]
        for summary_ref in summary_refs:
            summary = _read_and_validate(
                store,
                summary_ref,
                contract=cost_contract,
                label=f"{method} cost summary",
            )
            if (summary["episode_id"], summary["method_condition"]) != (
                episode_id,
                method,
            ):
                raise FullPackReconciliationError(f"{method} cost identity mismatch")
            if set(summary["axes"]) != set(COST_AXES):
                raise FullPackReconciliationError(f"{method} cost axes are incomplete")
            if any(
                axis["status"] not in {"measured", "unavailable"}
                for axis in summary["axes"].values()
            ):
                raise FullPackReconciliationError(f"{method} cost axis is unclassified")

        hidden_ref = trajectory["development_hidden_outcome_ref"]
        hidden_count += int(hidden_ref is not None)
        method_records.append(
            {
                "method_condition": method,
                "episode_id": episode_id,
                "trajectory_ref": record.trajectory_ref.to_dict(),
                "terminal_candidate_ref": terminal_ref,
                "cost_summary_refs": [reference.to_dict() for reference in summary_refs],
                "development_hidden_outcome_ref": hidden_ref,
                "lineage_complete": True,
                "all_cost_axes_classified": True,
            }
        )

    report = {
        "contract_version": "full-pack-runner-reconciliation-v2",
        "evaluation_scope": "excluded_development_conformance_only",
        "smoke_id": smoke_id,
        "analysis_population": "excluded",
        "g3_accepted": False,
        "g4b_authorized": False,
        "official_outcome": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "public_projection_sha256": projection,
        "source_smoke_report_ref": source_smoke_report_ref.to_dict(),
        "method_records": method_records,
        "reconciliation": {
            "method_set": list(_METHODS),
            "same_public_projection": True,
            "all_trajectories_verified": True,
            "all_cost_axes_classified": True,
            "matching_terminal_seals": True,
            "opaque_hidden_ref_count": hidden_count,
            "blocking_gaps": [
                "runtime_scenario_evidence_reconciliation",
                "official_public_terminal_hidden_authority",
                "g4b_campaign_authority",
            ],
        },
    }
    if paired_block_ref is not None and paired_block is not None:
        report["paired_block_ref"] = paired_block_ref.to_dict()
        report["method_order"] = list(paired_block["method_order"])
        report["actual_method_order"] = [
            record.method_condition for record in records
        ]
        report["method_order_verified"] = True
    reference = store.put_validated_json(
        f"full-pack-smokes/{smoke_id}/runner-reconciliation-v2",
        report,
        contract_key="full_pack_runner_reconciliation_v2",
        registry=registry,
    )
    return report, reference


def assemble_excluded_run_full_pack(
    store: ArtifactStore,
    *,
    events_path: Path,
    smoke_id: str,
    scenarios: Iterable[FullPackScenarioRecord],
) -> tuple[dict[str, Any], ArtifactRef, dict[str, Any], ArtifactRef]:
    """Assemble both CD9 reports from closed excluded Runner completion events."""

    try:
        event_lines = events_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FullPackReconciliationError("Runner events file is unavailable") from exc
    completed = []
    for line in event_lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FullPackReconciliationError("Runner events file is not valid JSONL") from exc
        if isinstance(event, dict) and event.get("event") == "sample_completed":
            completed.append(event)
    by_method = {
        str(event.get("method_condition")): event
        for event in completed
        if event.get("analysis_population") == "excluded"
    }
    if len(completed) != len(_METHODS) or set(by_method) != set(_METHODS):
        raise FullPackReconciliationError(
            "excluded Runner full pack requires exactly one M0-M5 completion"
        )
    paired_block_ref, paired_block = _validated_completion_paired_block(
        store,
        completed,
        events_path=events_path,
    )

    registry = ContractRegistry()
    artifact_gateway = MethodArtifactGateway(store)
    method_records: list[FullPackMethodRecord] = []
    runner_by_method: dict[str, FullPackRunnerArtifactRecord] = {}
    projections: set[str] = set()
    for method in _METHODS:
        event = by_method[method]
        pack_ref = _artifact_ref_from_event(event, "episode_pack_ref", method)
        pack = _read_registered_json(
            store,
            pack_ref,
            registry=registry,
            contract_key="episode_pack",
            label=f"{method} episode pack",
        )
        audit_only = pack["audit_only"]
        if (
            audit_only["analysis_population"],
            audit_only["method_condition_id"],
            audit_only["episode_id"],
        ) != ("excluded", method, event.get("sample_id")):
            raise FullPackReconciliationError(f"{method} episode-pack identity mismatch")
        if event.get("episode_pack_sha256") != pack["pack_sha256"]:
            raise FullPackReconciliationError(f"{method} episode-pack digest mismatch")
        if paired_block_ref is not None:
            if audit_only.get("paired_block_ref") != paired_block_ref.to_dict():
                raise FullPackReconciliationError(
                    f"{method} episode-pack paired-block reference mismatch"
                )
        elif "paired_block_ref" in audit_only:
            raise FullPackReconciliationError(
                f"{method} episode pack has an unexpected paired-block reference"
            )
        projection = pack["public_context"]["public_projection_sha256"]
        if event.get("public_projection_sha256") != projection:
            raise FullPackReconciliationError(f"{method} public projection mismatch")
        projections.add(projection)

        method_artifacts = event.get("method_artifacts")
        if not isinstance(method_artifacts, dict):
            raise FullPackReconciliationError(f"{method} method artifacts are missing")
        if method_artifacts.get("method_condition") != method:
            raise FullPackReconciliationError(f"{method} method artifact identity mismatch")
        candidate_ref = ArtifactRef(**method_artifacts["candidate_artifact_ref"])
        store.read_verified(candidate_ref)
        planning_ref_payload = method_artifacts.get("planning_artifact_ref")
        planning_ref = (
            ArtifactRef(**planning_ref_payload)
            if isinstance(planning_ref_payload, dict)
            else None
        )
        if planning_ref is not None:
            store.read_verified(planning_ref)
        skeleton_ref_payload = method_artifacts.get("skeleton_artifact_ref")
        skeleton_sha256 = method_artifacts.get("skeleton_project_sha256")
        if method in {"M4", "M5"}:
            if not isinstance(skeleton_ref_payload, dict) or not isinstance(
                skeleton_sha256, str
            ):
                raise FullPackReconciliationError(
                    f"{method} deterministic skeleton artifact is missing"
                )
            skeleton_ref = ArtifactRef(**skeleton_ref_payload)
            try:
                artifact_gateway.read_project(
                    ProjectCandidateEmission(skeleton_ref, skeleton_sha256)
                )
            except ValueError as exc:
                raise FullPackReconciliationError(
                    f"{method} deterministic skeleton artifact mismatch"
                ) from exc
        elif skeleton_ref_payload is not None or skeleton_sha256 is not None:
            raise FullPackReconciliationError(
                f"{method} must not claim a deterministic skeleton artifact"
            )
        skeleton_mode = str(method_artifacts["skeleton_mode"])
        if method in {"M0", "M1"}:
            skeleton_mode = "none"
        method_records.append(
            FullPackMethodRecord(
                method_condition=method,
                analysis_population="excluded",
                pack_sha256=pack["pack_sha256"],
                public_projection_sha256=projection,
                candidate_artifact_key=candidate_ref.key,
                candidate_artifact_sha256=candidate_ref.sha256,
                project_package_sha256=str(
                    method_artifacts["project_package_sha256"]
                ),
                skeleton_artifact_sha256=skeleton_sha256,
                planning_kind=method_artifacts.get("planning_kind"),
                planning_artifact_sha256=(
                    planning_ref.sha256 if planning_ref is not None else None
                ),
                h_status=str(method_artifacts["h_status"]),
                skeleton_mode=skeleton_mode,
            )
        )
        runner_by_method[method] = FullPackRunnerArtifactRecord(
            method,
            _artifact_ref_from_event(event, "canonical_trajectory_ref", method),
            paired_block_ref,
        )
    if len(projections) != 1:
        raise FullPackReconciliationError("excluded Runner methods use different projections")

    smoke_report, smoke_ref = reconcile_excluded_full_pack(
        store,
        smoke_id=smoke_id,
        methods=method_records,
        scenarios=scenarios,
    )
    runner_report, runner_ref = reconcile_full_pack_runner_artifacts(
        store,
        smoke_id=smoke_id,
        source_smoke_report_ref=smoke_ref,
        runner_artifacts=[
            runner_by_method[str(event["method_condition"])] for event in completed
        ],
    )
    return smoke_report, smoke_ref, runner_report, runner_ref


def assemble_excluded_run_full_pack_with_outcomes(
    store: ArtifactStore,
    *,
    events_path: Path,
    smoke_id: str,
    scenarios: Iterable[FullPackScenarioRecord],
) -> tuple[
    dict[str, Any],
    ArtifactRef,
    dict[str, Any],
    ArtifactRef,
    dict[str, Any],
    ArtifactRef,
]:
    """Add fail-closed development outcome reduction to the CD9 assembly."""

    smoke, smoke_ref, runner, runner_ref = assemble_excluded_run_full_pack(
        store,
        events_path=events_path,
        smoke_id=smoke_id,
        scenarios=scenarios,
    )
    completed = _excluded_completion_events(events_path)
    outcome_records: list[EpisodeOutcomeRecord] = []
    for method in _METHODS:
        event = completed[method]
        _, outcome_ref = reconcile_development_episode_outcome(
            store,
            public_evaluation_ref=_artifact_ref_from_event(
                event, "development_public_evaluation_ref", method
            ),
            trajectory_ref=_artifact_ref_from_event(
                event, "canonical_trajectory_ref", method
            ),
        )
        emitted_outcome = event.get("development_episode_outcome_ref")
        if emitted_outcome is not None:
            try:
                emitted_outcome_ref = ArtifactRef(**emitted_outcome)
            except TypeError as exc:
                raise FullPackReconciliationError(
                    f"{method} development episode outcome reference is invalid"
                ) from exc
            if emitted_outcome_ref != outcome_ref:
                raise FullPackReconciliationError(
                    f"{method} development episode outcome does not match Runner artifacts"
                )
        outcome_records.append(EpisodeOutcomeRecord(method, outcome_ref))
    outcome_report, outcome_ref = reconcile_excluded_full_pack_outcomes(
        store,
        smoke_id=smoke_id,
        source_runner_reconciliation_ref=runner_ref,
        outcomes=outcome_records,
    )
    return smoke, smoke_ref, runner, runner_ref, outcome_report, outcome_ref


def assemble_excluded_run_full_pack_with_cost_views(
    store: ArtifactStore,
    *,
    events_path: Path,
    smoke_id: str,
    scenarios: Iterable[FullPackScenarioRecord],
    reducer_policy_sha256: str,
) -> tuple[
    dict[str, Any],
    ArtifactRef,
    dict[str, Any],
    ArtifactRef,
    dict[str, Any],
    ArtifactRef,
]:
    """Add the verified G3b cost companion to a closed complete full pack."""

    smoke, smoke_ref, runner, runner_ref = assemble_excluded_run_full_pack(
        store,
        events_path=events_path,
        smoke_id=smoke_id,
        scenarios=scenarios,
    )
    completed = _excluded_completion_events(events_path)
    paired_block_payload = runner.get("paired_block_ref")
    if not isinstance(paired_block_payload, dict):
        raise FullPackReconciliationError(
            "G3b cost assembly requires a paired full-pack source"
        )
    try:
        paired_block_ref = ArtifactRef(**paired_block_payload)
    except TypeError as exc:
        raise FullPackReconciliationError(
            "G3b full-pack paired-block reference is invalid"
        ) from exc

    checkpoint_manifest_ref: ArtifactRef | None = None
    block_event_refs: tuple[ArtifactRef, ...] | None = None
    methods: list[MethodCostSource] = []
    for method in _METHODS:
        event = completed[method]
        audit = event.get("block_preparation_audit")
        if not isinstance(audit, dict):
            raise FullPackReconciliationError(
                f"{method} completion is missing block preparation audit"
            )
        if audit.get("paired_block_ref") != paired_block_ref.to_dict():
            raise FullPackReconciliationError(
                f"{method} block preparation audit belongs to another paired block"
            )
        manifest_payload = audit.get("checkpoint_manifest_ref")
        event_payloads = audit.get("block_event_refs")
        if not isinstance(manifest_payload, dict) or not isinstance(
            event_payloads, list
        ):
            raise FullPackReconciliationError(
                f"{method} block preparation lineage is incomplete"
            )
        try:
            current_manifest_ref = ArtifactRef(**manifest_payload)
            current_block_event_refs = tuple(
                ArtifactRef(**reference) for reference in event_payloads
            )
        except TypeError as exc:
            raise FullPackReconciliationError(
                f"{method} block preparation lineage is invalid"
            ) from exc
        if checkpoint_manifest_ref is None:
            checkpoint_manifest_ref = current_manifest_ref
            block_event_refs = current_block_event_refs
        elif (
            current_manifest_ref != checkpoint_manifest_ref
            or current_block_event_refs != block_event_refs
        ):
            raise FullPackReconciliationError(
                "completion block preparation lineages do not match"
            )
        methods.append(
            MethodCostSource(
                method,
                "completed",
                _artifact_ref_from_event(event, "canonical_trajectory_ref", method),
            )
        )

    if checkpoint_manifest_ref is None or block_event_refs is None:
        raise FullPackReconciliationError(
            "G3b cost assembly requires checkpoint lineage"
        )
    costs, costs_ref = reconcile_development_paired_block_costs(
        store,
        paired_block_ref=paired_block_ref,
        checkpoint_manifest_ref=checkpoint_manifest_ref,
        block_event_refs=block_event_refs,
        methods=methods,
        source_full_pack_runner_ref=runner_ref,
        reducer_policy_sha256=reducer_policy_sha256,
    )
    return smoke, smoke_ref, runner, runner_ref, costs, costs_ref


def _validated_completion_paired_block(
    store: ArtifactStore,
    completed: list[dict[str, Any]],
    *,
    events_path: Path,
) -> tuple[ArtifactRef | None, dict[str, Any] | None]:
    ref_payloads = [event.get("paired_block_ref") for event in completed]
    if not any(payload is not None for payload in ref_payloads):
        return None, None
    if not all(isinstance(payload, dict) for payload in ref_payloads):
        raise FullPackReconciliationError(
            "completion events have incomplete paired-block references"
        )
    try:
        references = [ArtifactRef(**payload) for payload in ref_payloads]
    except TypeError as exc:
        raise FullPackReconciliationError(
            "completion event has an invalid paired-block reference"
        ) from exc
    if len(set(references)) != 1:
        raise FullPackReconciliationError(
            "completion paired-block references do not match"
        )
    reference = references[0]
    try:
        block = load_development_paired_block(store, reference)
    except (ArtifactIntegrityError, ValueError) as exc:
        raise FullPackReconciliationError(
            "completion paired-block reference is invalid"
        ) from exc

    actual_order = [str(event.get("method_condition")) for event in completed]
    if actual_order != block["method_order"]:
        raise FullPackReconciliationError(
            "completion execution order does not match paired-block method order"
        )
    if [event.get("execution_ordinal") for event in completed] != list(range(6)):
        raise FullPackReconciliationError(
            "completion execution ordinals do not match paired-block method order"
        )
    identity_fields = {
        "paired_block_id": "paired_block_id",
        "semantic_instance_id": "semantic_instance_id",
        "replicate_id": "replicate_id",
        "decoding_seed": "requested_decoding_seed",
        "execution_schedule_seed": "execution_schedule_seed",
        "decoding_control_mode": "decoding_control_mode",
        "public_projection_sha256": "public_projection_sha256",
    }
    for event in completed:
        for event_field, block_field in identity_fields.items():
            if event.get(event_field) != block[block_field]:
                raise FullPackReconciliationError(
                    f"completion {event_field} does not match paired block"
                )

    freeze_path = events_path.parent / "measurement_freeze.json"
    try:
        measurement_freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FullPackReconciliationError(
            "paired completion measurement freeze is unavailable"
        ) from exc
    if not isinstance(measurement_freeze, dict):
        raise FullPackReconciliationError(
            "paired completion measurement freeze must be an object"
        )
    expected_fingerprint = freeze_fingerprint(measurement_freeze)
    if measurement_freeze.get("freeze_fingerprint") != expected_fingerprint:
        raise FullPackReconciliationError(
            "paired completion measurement freeze fingerprint mismatch"
        )
    if {
        event.get("freeze_fingerprint") for event in completed
    } != {expected_fingerprint}:
        raise FullPackReconciliationError(
            "completion events do not match the measurement freeze"
        )
    sample_records = measurement_freeze.get("samples")
    if not isinstance(sample_records, list):
        raise FullPackReconciliationError(
            "paired completion measurement freeze samples are missing"
        )
    by_sample_id = {
        record.get("sample_id"): record
        for record in sample_records
        if isinstance(record, dict)
    }
    for event in completed:
        record = by_sample_id.get(event.get("sample_id"))
        if not isinstance(record, dict) or record.get(
            "paired_block_ref"
        ) != reference.to_dict():
            raise FullPackReconciliationError(
                "measurement freeze paired-block reference mismatch"
            )
        if record.get("execution_ordinal") != event.get("execution_ordinal"):
            raise FullPackReconciliationError(
                "measurement freeze execution ordinal mismatch"
            )
    frozen_order = [
        str(record.get("method_condition"))
        for record in sample_records
        if isinstance(record, dict)
        and record.get("paired_block_ref") == reference.to_dict()
    ]
    if frozen_order != block["method_order"]:
        raise FullPackReconciliationError(
            "measurement freeze method order does not match paired block"
        )
    return reference, block


def _excluded_completion_events(events_path: Path) -> dict[str, dict[str, Any]]:
    try:
        lines = events_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FullPackReconciliationError("Runner events file is unavailable") from exc
    completed: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FullPackReconciliationError(
                "Runner events file is not valid JSONL"
            ) from exc
        if (
            isinstance(event, dict)
            and event.get("event") == "sample_completed"
            and event.get("analysis_population") == "excluded"
        ):
            completed.append(event)
    by_method = {str(event.get("method_condition")): event for event in completed}
    if len(completed) != len(_METHODS) or set(by_method) != set(_METHODS):
        raise FullPackReconciliationError(
            "excluded Runner full pack requires exactly one M0-M5 completion"
        )
    return by_method


def _artifact_ref_from_event(
    event: Mapping[str, Any],
    field: str,
    method: str,
) -> ArtifactRef:
    payload = event.get(field)
    if not isinstance(payload, dict):
        raise FullPackReconciliationError(f"{method} completion is missing {field}")
    try:
        return ArtifactRef(**payload)
    except TypeError as exc:
        raise FullPackReconciliationError(
            f"{method} completion has an invalid {field}"
        ) from exc


def _read_registered_json(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    registry: ContractRegistry,
    contract_key: str,
    label: str,
) -> dict[str, Any]:
    return _read_and_validate(
        store,
        reference,
        contract=registry.load_schema(contract_key),
        label=label,
    )


def _read_and_validate(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    contract,
    label: str,
) -> dict[str, Any]:
    try:
        payload = json.loads(store.read_verified(reference))
    except json.JSONDecodeError as exc:
        raise FullPackReconciliationError(f"{label} is not valid JSON") from exc
    errors = contract.validate(payload)
    if errors:
        raise FullPackReconciliationError(
            f"invalid {label}: " + "; ".join(errors)
        )
    return payload


def _validate_methods(records: tuple[FullPackMethodRecord, ...]) -> None:
    if len(records) != len(_METHODS):
        raise FullPackReconciliationError("full pack must contain exactly one M0-M5 record")
    by_method = {record.method_condition: record for record in records}
    if len(by_method) != len(records) or set(by_method) != set(_METHODS):
        raise FullPackReconciliationError("full pack method set must be exactly M0-M5")
    projections = {record.public_projection_sha256 for record in records}
    if len(projections) != 1:
        raise FullPackReconciliationError("M0-M5 must use one frozen public projection")
    for record in records:
        if record.analysis_population != "excluded":
            raise FullPackReconciliationError("full-pack smoke must remain excluded")
        for label, value in (
            ("pack_sha256", record.pack_sha256),
            ("public_projection_sha256", record.public_projection_sha256),
            ("candidate_artifact_sha256", record.candidate_artifact_sha256),
            ("project_package_sha256", record.project_package_sha256),
        ):
            _require_sha256(label, value)
        if not record.candidate_artifact_key:
            raise FullPackReconciliationError("candidate artifact key must be non-empty")
        if record.planning_artifact_sha256 is not None:
            _require_sha256("planning_artifact_sha256", record.planning_artifact_sha256)
        if record.skeleton_artifact_sha256 is not None:
            _require_sha256("skeleton_artifact_sha256", record.skeleton_artifact_sha256)

    if by_method["M0"].project_package_sha256 != by_method["M1"].project_package_sha256:
        raise FullPackReconciliationError("M0/M1 initial project packages are not matched")
    if (
        by_method["M3"].planning_artifact_sha256 is None
        or by_method["M3"].planning_artifact_sha256
        != by_method["M4"].planning_artifact_sha256
    ):
        raise FullPackReconciliationError("M3/M4 System-HIS artifacts are not matched")
    if by_method["M3"].candidate_artifact_key == by_method["M4"].candidate_artifact_key:
        raise FullPackReconciliationError("M3/M4 candidate artifact keys must be separate")
    if any(
        by_method[method].skeleton_artifact_sha256 is not None
        for method in {"M0", "M1", "M2", "M3"}
    ):
        raise FullPackReconciliationError(
            "non-skeleton methods must not claim deterministic skeleton artifacts"
        )
    if (
        by_method["M4"].skeleton_artifact_sha256 is None
        or by_method["M4"].skeleton_artifact_sha256
        != by_method["M5"].skeleton_artifact_sha256
    ):
        raise FullPackReconciliationError("M4/M5 deterministic skeletons are not matched")
    if by_method["M2"].planning_kind != "untyped_plan":
        raise FullPackReconciliationError("M2 must record an untyped plan")
    if by_method["M3"].skeleton_mode != "none_free_full_project":
        raise FullPackReconciliationError("M3 must record the no-skeleton path")


def _validate_scenarios(
    records: tuple[FullPackScenarioRecord, ...],
    projection: str,
) -> None:
    kinds = {record.scenario_kind for record in records}
    missing = sorted(_SCENARIOS - kinds)
    if missing:
        raise FullPackReconciliationError(
            "full-pack smoke is missing scenarios: " + ", ".join(missing)
        )
    for record in records:
        if record.scenario_kind not in _SCENARIOS:
            raise FullPackReconciliationError(
                f"unknown full-pack scenario: {record.scenario_kind}"
            )
        if record.analysis_population != "excluded":
            raise FullPackReconciliationError("scenario must remain excluded")
        if record.public_projection_sha256 != projection:
            raise FullPackReconciliationError("scenario public projection mismatch")

    _require_scenario(
        records,
        "success",
        lambda item: item.status == "passed"
        and item.facts.get("method_count") == 6
        and item.facts.get("scope") == "pre_candidate_emission_conformance",
    )
    _require_scenario(
        records,
        "h_repair",
        lambda item: item.method_condition == "M5"
        and item.status == "passed"
        and item.facts.get("his_corrections_used") == 1
        and item.facts.get("rerun_complete_h_validation") is True,
    )
    _require_scenario(
        records,
        "project_repair",
        lambda item: item.method_condition in {"M1", "M5"}
        and item.status == "passed"
        and item.facts.get("repair_calls_attempted") == 1
        and item.facts.get("repair_transitions") == 1
        and item.facts.get("rerun_performed") is True
        and item.facts.get("automatic_pass_credit") is True,
    )
    _require_scenario(
        records,
        "non_ready",
        lambda item: item.status in {"needs_clarification", "capability_gap"}
        and item.facts.get("generation_calls") == 0,
    )
    _require_scenario(
        records,
        "hidden_fail",
        lambda item: item.status == "fail"
        and item.facts.get("opaque_outcome_only") is True
        and item.facts.get("repair_after_hidden") is False,
    )
    _require_scenario(
        records,
        "infrastructure_not_run",
        lambda item: item.status == "not_run"
        and isinstance(item.facts.get("reason"), str)
        and bool(item.facts.get("reason"))
        and item.facts.get("replacement_episode") is False,
    )


def _require_scenario(records, kind: str, predicate) -> None:
    if not any(record.scenario_kind == kind and predicate(record) for record in records):
        raise FullPackReconciliationError(f"invalid {kind} scenario evidence")


def _require_sha256(label: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise FullPackReconciliationError(f"{label} must be lowercase SHA-256")
