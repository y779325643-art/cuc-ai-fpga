"""Fail-closed reducers for excluded M4 H-stage pre-candidate stops."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Iterable

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import reconcile_attempt_trajectory
from sr2fpga_agent.frozen_context import (
    capability_profile_id,
    context_from_validated_episode_pack,
    platform_profile_id,
    platform_profile_sha256,
    validate_episode_pack,
)
from sr2fpga_agent.his_validation import (
    first_failed_h_stage,
    validate_frozen_system_his_payload_h_stages,
)
from sr2fpga_agent.method_contract import method_policy_sha256
from sr2fpga_agent.models import PlatformProfile
from sr2fpga_agent.requirement_boundary import capability_profile_sha256
from sr2fpga_agent.system_his_capabilities import (
    load_system_his_backend_capabilities,
)
from sr2fpga_agent.system_his_schema import validate_registered_system_his_schema


_ZERO_COST_AXES = (
    "planner_parser_schema_retries",
    "outer_repair_attempts",
    "public_tool_calls",
    "hidden_evaluator_tool_calls",
    "hidden_infrastructure_retries",
    "eda_time",
    "hidden_evaluator_runtime",
)
_STATE_TRACE = (
    "method_prepared",
    "planning_artifact_emitted",
    "h_validated",
    "no_complete_candidate",
)


class PreCandidateOutcomeError(ValueError):
    pass


def read_verified_development_pre_candidate_stop_outcome(
    store: ArtifactStore,
    outcome_ref: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    """Read one stop outcome and rebuild every derived field from its refs."""

    contract_registry = registry or ContractRegistry()
    raw_payload = _read_json_object(
        store, outcome_ref, "development pre-candidate stop outcome"
    )
    contract_version = raw_payload.get("contract_version")
    contract_keys = {
        "development-pre-candidate-stop-outcome-v1": (
            "development_pre_candidate_stop_outcome"
        ),
        "development-pre-candidate-stop-outcome-v2": (
            "development_pre_candidate_stop_outcome_v2"
        ),
    }
    contract_key = contract_keys.get(contract_version)
    if contract_key is None:
        raise PreCandidateOutcomeError(
            "unsupported development pre-candidate stop outcome version"
        )
    errors = contract_registry.load_schema(contract_key).validate(raw_payload)
    if errors:
        raise PreCandidateOutcomeError(
            "invalid development pre-candidate stop outcome: " + "; ".join(errors)
        )
    payload = raw_payload
    without_id = {key: value for key, value in payload.items() if key != "outcome_id"}
    expected_id = "pre-candidate-stop-outcome-" + hashlib.sha256(
        _canonical_json(without_id)
    ).hexdigest()
    if payload["outcome_id"] != expected_id:
        raise PreCandidateOutcomeError("pre-candidate stop outcome ID mismatch")
    platform = None
    if contract_version == "development-pre-candidate-stop-outcome-v2":
        try:
            platform = PlatformProfile(**payload["platform_profile"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PreCandidateOutcomeError("invalid committed platform profile") from exc
    rebuilt, rebuilt_ref = reconcile_development_pre_candidate_stop_outcome(
        store,
        episode_pack_ref=ArtifactRef(**payload["episode_pack_ref"]),
        planning_artifact_ref=ArtifactRef(**payload["planning_artifact_ref"]),
        method_event_refs=(
            ArtifactRef(**reference) for reference in payload["method_event_refs"]
        ),
        trajectory_ref=ArtifactRef(**payload["trajectory_ref"]),
        platform=platform,
        registry=contract_registry,
    )
    if rebuilt != payload or rebuilt_ref != outcome_ref:
        raise PreCandidateOutcomeError(
            "pre-candidate stop outcome does not rebuild from source artifacts"
        )
    return payload


def reconcile_development_pre_candidate_stop_outcome(
    store: ArtifactStore,
    *,
    episode_pack_ref: ArtifactRef,
    planning_artifact_ref: ArtifactRef,
    method_event_refs: Iterable[ArtifactRef],
    trajectory_ref: ArtifactRef,
    platform: PlatformProfile | None = None,
    registry: ContractRegistry | None = None,
) -> tuple[dict[str, Any], ArtifactRef]:
    """Rebuild a retained M4 H-stage design-stop only from verified artifacts.

    Omitting ``platform`` retains the registered v1 M4/H0 writer for historical
    artifact compatibility. Supplying the committed platform writes v2 and
    deterministically re-runs H0-H3 from the frozen episode pack and planning
    artifact.
    """

    contract_registry = registry or ContractRegistry()
    episode_pack = _read_registered(
        store,
        episode_pack_ref,
        contract_registry,
        "episode_pack",
        "episode pack",
    )
    pack_errors = validate_episode_pack(episode_pack)
    if pack_errors:
        raise PreCandidateOutcomeError(
            "episode pack digest mismatch: " + "; ".join(pack_errors)
        )
    audit = episode_pack["audit_only"]
    if audit["analysis_population"] != "excluded":
        raise PreCandidateOutcomeError("pre-candidate stop requires excluded input")
    if audit["method_condition_id"] != "M4":
        raise PreCandidateOutcomeError("pre-candidate stop requires M4")
    episode_id = str(audit["episode_id"])

    planning = _read_json_object(store, planning_artifact_ref, "planning artifact")
    if platform is None:
        h0_diagnostics = validate_registered_system_his_schema(planning)
        if not h0_diagnostics:
            raise PreCandidateOutcomeError(
                "planning artifact does not fail registered H0"
            )
        contract_version = "development-pre-candidate-stop-outcome-v1"
        contract_key = "development_pre_candidate_stop_outcome"
        failure_stage = "h0"
        h_validation = None
    else:
        expected_platform_sha256 = episode_pack["public_context"][
            "platform_profile_sha256"
        ]
        if platform_profile_sha256(platform) != expected_platform_sha256:
            raise PreCandidateOutcomeError(
                "platform profile does not match the frozen episode pack"
            )
        if (
            platform_profile_id(platform)
            != episode_pack["public_context"]["platform_profile_id"]
        ):
            raise PreCandidateOutcomeError(
                "platform profile ID does not match the frozen episode pack"
            )
        backend_capabilities = load_system_his_backend_capabilities()
        expected_capability_sha256 = capability_profile_sha256(
            backend_capabilities
        )
        if (
            episode_pack["public_context"]["capability_profile_sha256"]
            != expected_capability_sha256
        ):
            raise PreCandidateOutcomeError(
                "capability profile does not match the registered H-stage backend"
            )
        if (
            episode_pack["public_context"]["capability_profile_id"]
            != capability_profile_id(backend_capabilities.registry_version)
        ):
            raise PreCandidateOutcomeError(
                "capability profile ID does not match the registered H-stage backend"
            )
        context = context_from_validated_episode_pack(episode_pack)
        h_report = validate_frozen_system_his_payload_h_stages(
            context,
            planning,
            platform=platform,
        )
        failure_stage = first_failed_h_stage(h_report)
        if failure_stage is None or h_report.get("passed") is not False:
            raise PreCandidateOutcomeError(
                "planning artifact does not produce a failed H0-H3 report"
            )
        stage_statuses = {
            stage: h_report[stage]["status"]
            for stage in ("h0", "h1", "h2", "h3")
        }
        if stage_statuses != _expected_h_statuses(failure_stage):
            raise PreCandidateOutcomeError(
                "H-stage report does not preserve short-circuit semantics"
            )
        contract_version = "development-pre-candidate-stop-outcome-v2"
        contract_key = "development_pre_candidate_stop_outcome_v2"
        h_validation = {
            "report_sha256": hashlib.sha256(_canonical_json(h_report)).hexdigest(),
            "failed_stage": failure_stage,
            "stage_statuses": stage_statuses,
        }
    event_references = tuple(method_event_refs)
    events = _verify_method_events(
        store,
        event_references,
        episode_id=episode_id,
        planning_sha256=planning_artifact_ref.sha256,
        failure_stage=failure_stage,
        require_closed_episode_stream=platform is not None,
    )
    failure_payload = events[-1]["payload"]
    failure = {
        "stage": failure_payload["failure_stage"],
        "error_type": failure_payload["error_type"],
        "message": failure_payload["message"],
    }

    trajectory = _read_registered(
        store,
        trajectory_ref,
        contract_registry,
        "trajectory_v2",
        "trajectory-v2",
    )
    if (trajectory["episode_id"], trajectory["method_condition"]) != (
        episode_id,
        "M4",
    ):
        raise PreCandidateOutcomeError("trajectory identity mismatch")
    if trajectory["failure_origin"] != "synthetic_injected":
        raise PreCandidateOutcomeError(
            "pre-candidate stop fixture requires synthetic_injected origin"
        )
    if len(trajectory["attempts"]) != 1:
        raise PreCandidateOutcomeError("M4 pre-candidate stop requires one attempt")
    attempt = trajectory["attempts"][0]
    if attempt["output_artifact_hashes"] != [planning_artifact_ref.sha256]:
        raise PreCandidateOutcomeError(
            "trajectory output does not bind the stopped planning artifact"
        )
    if platform is not None:
        required_input_hashes = {
            episode_pack_ref.sha256,
            episode_pack["public_context"]["public_projection_sha256"],
        }
        if not required_input_hashes.issubset(attempt["input_artifact_hashes"]):
            raise PreCandidateOutcomeError(
                "trajectory input does not bind the frozen episode pack"
            )
    trajectory_status = {
        "lineage_complete": trajectory["lineage_complete"],
        "missing_lineage_reasons": trajectory["missing_lineage_reasons"],
        "terminal_candidate_ref": trajectory["terminal_candidate_ref"],
        "development_terminal_selection_ref": trajectory.get(
            "development_terminal_selection_ref"
        ),
        "development_selected_public_outcome_ref": trajectory.get(
            "development_selected_public_outcome_ref"
        ),
        "development_terminal_public_outcome_ref": trajectory.get(
            "development_terminal_public_outcome_ref"
        ),
        "development_hidden_outcome_ref": trajectory.get(
            "development_hidden_outcome_ref"
        ),
        "development_hidden_conformance_outcome_ref": trajectory.get(
            "development_hidden_conformance_outcome_ref"
        ),
    }
    expected_trajectory_status = {
        "lineage_complete": False,
        "missing_lineage_reasons": ["terminal_candidate_ref_missing"],
        "terminal_candidate_ref": None,
        "development_terminal_selection_ref": None,
        "development_selected_public_outcome_ref": None,
        "development_terminal_public_outcome_ref": None,
        "development_hidden_outcome_ref": None,
        "development_hidden_conformance_outcome_ref": None,
    }
    if trajectory_status != expected_trajectory_status:
        raise PreCandidateOutcomeError(
            "trajectory is not a closed pre-candidate design stop"
        )

    cost_summary_refs = tuple(
        ArtifactRef(**item["cost_summary_ref"])
        for item in trajectory["attempts"]
    )
    rebuilt = reconcile_attempt_trajectory(
        store,
        cost_summary_refs,
        terminal_candidate_ref=None,
        terminal_candidate_missing_reason="terminal_candidate_ref_missing",
        registry=contract_registry,
    )
    if rebuilt.artifact_ref != trajectory_ref or rebuilt.payload != trajectory:
        raise PreCandidateOutcomeError(
            "trajectory does not rebuild from raw attempt events"
        )
    cost = _reconcile_stop_costs(store, cost_summary_refs, contract_registry)

    stage_outcomes = _stage_outcomes(failure_stage)
    without_id = {
        "contract_version": contract_version,
        "evaluation_scope": "excluded_development_conformance_only",
        "episode_id": episode_id,
        "method_condition": "M4",
        "analysis_population": "excluded",
        "failure_origin": "synthetic_injected",
        "episode_pack_ref": episode_pack_ref.to_dict(),
        "public_projection_sha256": episode_pack["public_context"][
            "public_projection_sha256"
        ],
        "method_policy_sha256": method_policy_sha256("M4"),
        "planning_kind": "system_his",
        "planning_artifact_ref": planning_artifact_ref.to_dict(),
        "method_event_refs": [reference.to_dict() for reference in event_references],
        "source_method_events_sha256": hashlib.sha256(
            _canonical_json([event["event_id"] for event in events])
        ).hexdigest(),
        "state_trace": list(_STATE_TRACE),
        "final_state": "no_complete_candidate",
        "failure": failure,
        "trajectory_ref": trajectory_ref.to_dict(),
        "cost_summary_refs": [reference.to_dict() for reference in cost_summary_refs],
        "trajectory_status": trajectory_status,
        "cost": cost,
        "stage_outcomes": stage_outcomes,
        "repair": {
            "reconciliation_status": "complete",
            "calls_attempted": 0,
            "transitions": 0,
            "successes": 0,
            "diagnosis_count": 0,
            "valid_patch_count": 0,
            "rerun_count": 0,
            "by_scope": {
                "system_his": {"calls_attempted": 0, "transitions": 0},
                "project": {"calls_attempted": 0, "transitions": 0},
            },
            "skip_reason": "method_contract_disallows_system_his_correction",
        },
        "missingness": {
            "classification": "design_outcome",
            "reason": "h0_failed_before_complete_candidate",
            "retained": True,
            "replacement_allowed": False,
        },
        "development_vpp_l3_status": "evaluated",
        "development_vpp_l3": False,
        "development_vpp_l3_reasons": [
            f"{failure_stage}_failed",
            "no_complete_candidate",
        ],
        "vpp_l3_status": "not_evaluated",
        "vpp_l3": None,
        "vpp_l3_reasons": [
            "official_hidden_outcome_unavailable",
            "public_authority_not_official",
        ],
        "denominator": {
            "population": "excluded",
            "retained": True,
            "replacement_allowed": False,
        },
        "reducer_visible": True,
        "generation_visible": False,
        "repair_visible": False,
        "terminal_selection_authority": False,
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    if platform is not None:
        without_id["platform_profile"] = asdict(platform)
        without_id["h_validation"] = h_validation
        without_id["missingness"] = {
            **without_id["missingness"],
            "reason": f"{failure_stage}_failed_before_complete_candidate",
        }
    payload = {
        **without_id,
        "outcome_id": "pre-candidate-stop-outcome-"
        + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
    }
    artifact_key = f"pre-candidate-stop-outcomes/{episode_id}/M4"
    if platform is not None:
        artifact_key += "/v2"
    reference = store.put_validated_json(
        artifact_key,
        payload,
        contract_key=contract_key,
        registry=contract_registry,
    )
    return payload, reference


def _verify_method_events(
    store: ArtifactStore,
    references: tuple[ArtifactRef, ...],
    *,
    episode_id: str,
    planning_sha256: str,
    failure_stage: str,
    require_closed_episode_stream: bool,
) -> list[dict[str, Any]]:
    if len(references) != 5 or len(set(references)) != len(references):
        raise PreCandidateOutcomeError(
            "pre-candidate stop requires five distinct method events"
        )
    events = [
        _read_json_object(store, reference, "method event")
        for reference in references
    ]
    for index, (reference, event) in enumerate(zip(references, events)):
        if event.get("event_version") != "trusted-core-event-v1":
            raise PreCandidateOutcomeError("unsupported method event version")
        if event.get("episode_id") != episode_id or event.get("sequence") != index:
            raise PreCandidateOutcomeError("method event identity or order mismatch")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not store.has_event_id(event_id):
            raise PreCandidateOutcomeError("method event is not append-only verified")
        unsigned = {key: value for key, value in event.items() if key != "event_id"}
        expected_id = "event-" + hashlib.sha256(_canonical_json(unsigned)).hexdigest()
        if event_id != expected_id or not reference.key.endswith(f"-{event_id}"):
            raise PreCandidateOutcomeError("method event content ID mismatch")
    expected_types = (
        "episode_state_transition",
        "shared_artifact_consumed",
        "episode_state_transition",
        "episode_state_transition",
        "episode_state_transition",
    )
    if tuple(event["event_type"] for event in events) != expected_types:
        raise PreCandidateOutcomeError("method event type sequence mismatch")
    expected_payloads = (
        {"state": "method_prepared", "method_condition_id": "M4"},
        {
            "method_condition_id": "M4",
            "artifact_kind": "system_his",
            "artifact_sha256": planning_sha256,
        },
        {
            "state": "planning_artifact_emitted",
            "method_condition_id": "M4",
            "planning_kind": "system_his",
            "artifact_sha256": planning_sha256,
        },
        {
            "state": "h_validated",
            "method_condition_id": "M4",
            "passed": False,
            "failed_h_stage": failure_stage,
        },
        {
            "state": "no_complete_candidate",
            "method_condition_id": "M4",
            "failure_stage": failure_stage,
            "error_type": "HValidationFailed",
            "message": "method contract does not allow System-HIS correction",
        },
    )
    if tuple(event["payload"] for event in events) != expected_payloads:
        raise PreCandidateOutcomeError("method event payload sequence mismatch")
    if require_closed_episode_stream and references != store.event_refs(episode_id):
        raise PreCandidateOutcomeError(
            "pre-candidate stop method events are not the complete episode stream"
        )
    return events


def _reconcile_stop_costs(
    store: ArtifactStore,
    references: tuple[ArtifactRef, ...],
    registry: ContractRegistry,
) -> dict[str, Any]:
    if len(references) != 1:
        raise PreCandidateOutcomeError("M4 pre-candidate stop requires one cost summary")
    summary = _read_registered(
        store,
        references[0],
        registry,
        "cost_summary",
        "cost summary",
    )
    axes = summary["axes"]
    logical_calls = axes["logical_model_calls"]
    if logical_calls != {"status": "measured", "value": 1, "reason": None}:
        raise PreCandidateOutcomeError("M4 H-stage fixture requires one model call")
    for axis_name in _ZERO_COST_AXES:
        if axes[axis_name] != {"status": "measured", "value": 0, "reason": None}:
            raise PreCandidateOutcomeError(
                f"pre-candidate stop requires measured zero {axis_name}"
            )
    unavailable_axes = sorted(
        name for name, axis in axes.items() if axis["status"] == "unavailable"
    )
    return {
        "all_axes_classified": True,
        "logical_model_calls": 1,
        "zero_axes": list(_ZERO_COST_AXES),
        "unavailable_axes": unavailable_axes,
    }


def _expected_h_statuses(failure_stage: str) -> dict[str, str]:
    stages = ("h0", "h1", "h2", "h3")
    if failure_stage not in stages:
        raise PreCandidateOutcomeError("unsupported failed H stage")
    failure_index = stages.index(failure_stage)
    return {
        stage: (
            "pass"
            if index < failure_index
            else "fail"
            if index == failure_index
            else "not_run"
        )
        for index, stage in enumerate(stages)
    }


def _stage_outcomes(failure_stage: str) -> dict[str, dict[str, str | None]]:
    reasons = {
        "h0": "registered_schema_validation_failed",
        "h1": "well_formedness_validation_failed",
        "h2": "lowerability_validation_failed",
        "h3": "requirement_fidelity_validation_failed",
    }
    statuses = _expected_h_statuses(failure_stage)
    downstream_reason = f"upstream_{failure_stage}_failed"
    outcomes: dict[str, dict[str, str | None]] = {
        "planning": {"status": "pass", "reason": None}
    }
    for stage in ("h0", "h1", "h2", "h3"):
        status = statuses[stage]
        outcomes[stage] = {
            "status": status,
            "reason": (
                reasons[stage]
                if status == "fail"
                else downstream_reason
                if status == "not_run"
                else None
            ),
        }
    for stage in (
        "project_emission",
        "l0",
        "l1",
        "public_l2",
        "l3",
        "l4_open",
        "l4_commercial",
    ):
        outcomes[stage] = {"status": "not_run", "reason": downstream_reason}
    return outcomes


def _read_registered(
    store: ArtifactStore,
    reference: ArtifactRef,
    registry: ContractRegistry,
    contract_key: str,
    label: str,
) -> dict[str, Any]:
    payload = _read_json_object(store, reference, label)
    errors = registry.load_schema(contract_key).validate(payload)
    if errors:
        raise PreCandidateOutcomeError(
            f"invalid {label}: " + "; ".join(errors)
        )
    return payload


def _read_json_object(
    store: ArtifactStore,
    reference: ArtifactRef,
    label: str,
) -> dict[str, Any]:
    try:
        payload = json.loads(store.read_verified(reference))
    except json.JSONDecodeError as exc:
        raise PreCandidateOutcomeError(f"{label} is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise PreCandidateOutcomeError(f"{label} must be a JSON object")
    return payload


def _canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
