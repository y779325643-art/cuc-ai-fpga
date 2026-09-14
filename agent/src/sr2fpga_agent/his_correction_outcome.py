"""Artifact-derived acceptance for excluded M5 System-HIS correction."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Iterable

from sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    canonical_json_bytes as _canonical_json,
)
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import reconcile_cost_events
from sr2fpga_agent.episode_outcome import read_verified_development_episode_outcome
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
from sr2fpga_agent.project_contract import project_package_sha256
from sr2fpga_agent.requirement_boundary import capability_profile_sha256
from sr2fpga_agent.system_his_capabilities import load_system_his_backend_capabilities


_H_STAGES = ("h0", "h1", "h2", "h3")
_STATE_TRACE = (
    "method_prepared",
    "planning_artifact_emitted",
    "h_validated",
    "his_correction_requested",
    "planning_artifact_emitted",
    "h_validated",
    "candidate_emitted",
)


class HisCorrectionOutcomeError(ValueError):
    pass


def read_verified_development_his_correction_outcome(
    store: ArtifactStore,
    outcome_ref: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    contract_registry = registry or ContractRegistry()
    raw = _read_json(store, outcome_ref, "development PC correction outcome")
    key = {
        "development-his-correction-outcome-v1": "development_his_correction_outcome",
        "development-his-correction-outcome-v2": "development_his_correction_outcome_v2",
    }.get(raw.get("contract_version"))
    if key is None:
        raise HisCorrectionOutcomeError("unsupported PC correction outcome version")
    payload = _read_registered(
        store,
        outcome_ref,
        contract_registry,
        key,
        "development HIS correction outcome",
    )
    without_id = {key: value for key, value in payload.items() if key != "outcome_id"}
    if payload["outcome_id"] != "his-correction-outcome-" + hashlib.sha256(
        _canonical_json(without_id)
    ).hexdigest():
        raise HisCorrectionOutcomeError("HIS correction outcome ID mismatch")
    rebuilt, rebuilt_ref = reconcile_development_his_correction_outcome(
        store,
        episode_pack_ref=ArtifactRef(**payload["episode_pack_ref"]),
        initial_his_ref=ArtifactRef(**payload["initial_his_ref"]),
        corrected_his_ref=ArtifactRef(**payload["corrected_his_ref"]),
        method_event_refs=(ArtifactRef(**item) for item in payload["method_event_refs"]),
        candidate_artifact_ref=ArtifactRef(**payload["candidate_artifact_ref"]),
        trajectory_ref=ArtifactRef(**payload["trajectory_ref"]),
        development_episode_outcome_ref=ArtifactRef(
            **payload["development_episode_outcome_ref"]
        ),
        platform=PlatformProfile(**payload["platform_profile"]),
        registry=contract_registry,
    )
    if rebuilt != payload or rebuilt_ref != outcome_ref:
        raise HisCorrectionOutcomeError(
            "HIS correction outcome does not rebuild from source artifacts"
        )
    return payload


def reconcile_development_his_correction_outcome(
    store: ArtifactStore,
    *,
    episode_pack_ref: ArtifactRef,
    initial_his_ref: ArtifactRef,
    corrected_his_ref: ArtifactRef,
    method_event_refs: Iterable[ArtifactRef],
    candidate_artifact_ref: ArtifactRef,
    trajectory_ref: ArtifactRef,
    development_episode_outcome_ref: ArtifactRef,
    platform: PlatformProfile,
    registry: ContractRegistry | None = None,
) -> tuple[dict[str, Any], ArtifactRef]:
    contract_registry = registry or ContractRegistry()
    pack = _read_registered(
        store, episode_pack_ref, contract_registry, "episode_pack", "episode pack"
    )
    errors = validate_episode_pack(pack)
    if errors:
        raise HisCorrectionOutcomeError("episode pack digest mismatch: " + "; ".join(errors))
    audit = pack["audit_only"]
    if audit["analysis_population"] != "excluded" or audit["method_condition_id"] != "M5":
        raise HisCorrectionOutcomeError("HIS correction outcome requires excluded M5")
    episode_id = str(audit["episode_id"])
    public = pack["public_context"]
    if platform_profile_id(platform) != public["platform_profile_id"]:
        raise HisCorrectionOutcomeError("platform profile ID mismatch")
    if platform_profile_sha256(platform) != public["platform_profile_sha256"]:
        raise HisCorrectionOutcomeError("platform profile hash mismatch")
    capabilities = load_system_his_backend_capabilities()
    capability_id = capability_profile_id(capabilities.registry_version)
    capability_sha256 = capability_profile_sha256(capabilities)
    if (public["capability_profile_id"], public["capability_profile_sha256"]) != (
        capability_id,
        capability_sha256,
    ):
        raise HisCorrectionOutcomeError("backend capability profile drift")

    if initial_his_ref == corrected_his_ref or initial_his_ref.sha256 == corrected_his_ref.sha256:
        raise HisCorrectionOutcomeError("corrected HIS must be a distinct artifact")
    initial_his = _read_json(store, initial_his_ref, "initial HIS")
    corrected_his = _read_json(store, corrected_his_ref, "corrected HIS")
    context = context_from_validated_episode_pack(pack)
    initial_report = validate_frozen_system_his_payload_h_stages(
        context, initial_his, platform=platform
    )
    failed_stage = first_failed_h_stage(initial_report)
    if failed_stage not in _H_STAGES or initial_report.get("passed") is not False:
        raise HisCorrectionOutcomeError("initial HIS must fail exactly one ordered H stage")
    initial_statuses = {stage: initial_report[stage]["status"] for stage in _H_STAGES}
    if initial_statuses != _expected_initial_statuses(failed_stage):
        raise HisCorrectionOutcomeError("initial H report violates short-circuit order")
    corrected_report = validate_frozen_system_his_payload_h_stages(
        context, corrected_his, platform=platform
    )
    corrected_statuses = {stage: corrected_report[stage]["status"] for stage in _H_STAGES}
    if corrected_report.get("passed") is not True or set(corrected_statuses.values()) != {"pass"}:
        raise HisCorrectionOutcomeError("corrected HIS must pass complete H0-H3 rerun")

    event_refs = tuple(method_event_refs)
    events = _verify_method_events(
        store,
        event_refs,
        episode_id=episode_id,
        initial_sha256=initial_his_ref.sha256,
        corrected_sha256=corrected_his_ref.sha256,
        failed_stage=failed_stage,
    )
    candidate_payload = _read_json(store, candidate_artifact_ref, "candidate artifact")
    try:
        candidate = GeneratedProject(
            str(candidate_payload["project_name"]), dict(candidate_payload["files"])
        )
        candidate_his = json.loads(candidate.files["system_his.json"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise HisCorrectionOutcomeError("candidate does not contain a valid corrected HIS") from exc
    if candidate_his != corrected_his:
        raise HisCorrectionOutcomeError("candidate was not derived from the corrected HIS")
    package_sha256 = project_package_sha256(candidate)
    candidate_event = events[-1]["payload"]
    if candidate_event["artifact_sha256"] != candidate_artifact_ref.sha256:
        raise HisCorrectionOutcomeError("candidate event artifact mismatch")
    if candidate_event["project_package_sha256"] != package_sha256:
        raise HisCorrectionOutcomeError("candidate event project package mismatch")

    episode_outcome = read_verified_development_episode_outcome(
        store, development_episode_outcome_ref, registry=contract_registry
    )
    if (episode_outcome["episode_id"], episode_outcome["method_condition"]) != (
        episode_id,
        "M5",
    ):
        raise HisCorrectionOutcomeError("development episode outcome identity mismatch")
    if episode_outcome["trajectory_ref"] != trajectory_ref.to_dict():
        raise HisCorrectionOutcomeError("development episode outcome trajectory mismatch")
    terminal_ref = ArtifactRef(**episode_outcome["terminal_candidate_ref"])
    terminal_project = store.read_sealed_project(terminal_ref)
    if json.loads(terminal_project.files.get("system_his.json", "null")) != corrected_his:
        raise HisCorrectionOutcomeError("terminal candidate does not preserve corrected HIS")

    trajectory = _read_registered(
        store, trajectory_ref, contract_registry, "trajectory_v2", "trajectory-v2"
    )
    if trajectory["terminal_candidate_ref"] != terminal_ref.to_dict():
        raise HisCorrectionOutcomeError("trajectory terminal candidate mismatch")
    cost_refs = tuple(ArtifactRef(**item["cost_summary_ref"]) for item in trajectory["attempts"])
    cost = _reconcile_cost(
        store,
        cost_refs,
        trajectory["attempts"],
        contract_registry,
    )
    legacy = (
        cost["logical_model_stages"] == {"req2his": 1, "system_his_repair": 1, "his2project": 1}
        and cost["project_repairs"] == 0
    )
    version = "v1" if legacy else "v2"
    development_status = (
        "completed"
        if episode_outcome["development_vpp_l3_status"] == "evaluated"
        else "infrastructure_not_run"
    )
    without_id = {
        "contract_version": f"development-his-correction-outcome-{version}",
        "evaluation_scope": "excluded_development_conformance_only",
        "episode_id": episode_id,
        "method_condition": "M5",
        "analysis_population": "excluded",
        "failure_origin": trajectory["failure_origin"],
        "episode_pack_ref": episode_pack_ref.to_dict(),
        "public_projection_sha256": public["public_projection_sha256"],
        "method_policy_sha256": method_policy_sha256("M5"),
        "platform_profile": asdict(platform),
        "platform_profile_id": public["platform_profile_id"],
        "platform_profile_sha256": public["platform_profile_sha256"],
        "capability_profile_id": capability_id,
        "capability_profile_sha256": capability_sha256,
        "initial_his_ref": initial_his_ref.to_dict(),
        "corrected_his_ref": corrected_his_ref.to_dict(),
        "correction_lineage": {
            "failed_stage": failed_stage,
            "input_artifact_sha256": initial_his_ref.sha256,
            "parent_artifact_sha256": initial_his_ref.sha256,
            "corrected_artifact_sha256": corrected_his_ref.sha256,
            "correction_count": 1,
            "extra_correction_count": 0,
        },
        "h_validation": {
            "initial_report_sha256": hashlib.sha256(_canonical_json(initial_report)).hexdigest(),
            "initial_failed_stage": failed_stage,
            "initial_stage_statuses": initial_statuses,
            "corrected_report_sha256": hashlib.sha256(_canonical_json(corrected_report)).hexdigest(),
            "corrected_stage_statuses": corrected_statuses,
        },
        "method_event_refs": [item.to_dict() for item in event_refs],
        "source_method_events_sha256": hashlib.sha256(
            _canonical_json([event["event_id"] for event in events])
        ).hexdigest(),
        "state_trace": list(_STATE_TRACE),
        "candidate_artifact_ref": candidate_artifact_ref.to_dict(),
        "project_package_sha256": package_sha256,
        "trajectory_ref": trajectory_ref.to_dict(),
        "terminal_candidate_ref": terminal_ref.to_dict(),
        "development_episode_outcome_ref": development_episode_outcome_ref.to_dict(),
        "cost_summary_refs": [item.to_dict() for item in cost_refs],
        "cost": cost,
        "development_outcome": {
            "status": development_status,
            "development_vpp_l3": episode_outcome["development_vpp_l3"],
            "official_vpp_l3_status": "not_evaluated",
        },
        "comparison_status": "m5_development_conformance_only_unpaired",
        "denominator": {"population": "excluded", "retained": True, "replacement_allowed": False},
        "reducer_visible": True,
        "generation_visible": False,
        "repair_visible": False,
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    payload = {
        **without_id,
        "outcome_id": "his-correction-outcome-"
        + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
    }
    ref = store.put_validated_json(
        f"his-correction-outcomes/{episode_id}/M5" + ("/v2" if not legacy else ""),
        payload,
        contract_key="development_his_correction_outcome" if legacy else "development_his_correction_outcome_v2",
        registry=contract_registry,
    )
    return payload, ref


def _verify_method_events(store, refs, *, episode_id, initial_sha256, corrected_sha256, failed_stage):
    if len(refs) != 8 or len(set(refs)) != 8:
        raise HisCorrectionOutcomeError("M5 correction requires eight distinct method events")
    events = [_read_json(store, ref, "method event") for ref in refs]
    expected_types = (
        "episode_state_transition", "shared_artifact_consumed",
        "episode_state_transition", "episode_state_transition",
        "episode_state_transition", "episode_state_transition",
        "episode_state_transition", "episode_state_transition",
    )
    if tuple(event.get("event_type") for event in events) != expected_types:
        raise HisCorrectionOutcomeError("method event type sequence mismatch")
    for index, (ref, event) in enumerate(zip(refs, events)):
        if event.get("episode_id") != episode_id or event.get("sequence") != index:
            raise HisCorrectionOutcomeError("method event identity or order mismatch")
        if not store.has_event_id(str(event.get("event_id", ""))):
            raise HisCorrectionOutcomeError("method event is not append-only verified")
        unsigned = {key: value for key, value in event.items() if key != "event_id"}
        expected_id = "event-" + hashlib.sha256(_canonical_json(unsigned)).hexdigest()
        if event["event_id"] != expected_id or not ref.key.endswith("-" + expected_id):
            raise HisCorrectionOutcomeError("method event content ID mismatch")
    expected_payloads = (
        {"state": "method_prepared", "method_condition_id": "M5"},
        {"method_condition_id": "M5", "artifact_kind": "system_his", "artifact_sha256": initial_sha256},
        {"state": "planning_artifact_emitted", "method_condition_id": "M5", "planning_kind": "system_his", "artifact_sha256": initial_sha256},
        {"state": "h_validated", "method_condition_id": "M5", "passed": False, "failed_h_stage": failed_stage},
        {"state": "his_correction_requested", "method_condition_id": "M5", "failed_h_stage": failed_stage, "input_artifact_sha256": initial_sha256},
        {"state": "planning_artifact_emitted", "method_condition_id": "M5", "planning_kind": "system_his", "artifact_sha256": corrected_sha256, "correction_attempt": 1, "parent_artifact_sha256": initial_sha256},
        {"state": "h_validated", "method_condition_id": "M5", "passed": True, "failed_h_stage": None},
    )
    if tuple(event["payload"] for event in events[:7]) != expected_payloads:
        raise HisCorrectionOutcomeError("method event payload sequence mismatch")
    if events[7]["payload"].get("state") != "candidate_emitted" or events[7]["payload"].get("method_condition_id") != "M5":
        raise HisCorrectionOutcomeError("candidate emission does not follow corrected H pass")
    complete = store.event_refs(episode_id)
    if tuple(complete[:8]) != refs:
        raise HisCorrectionOutcomeError("method events are not the authoritative episode prefix")
    return events


def _reconcile_cost(store, refs, attempts, registry):
    if len(refs) != len(attempts):
        raise HisCorrectionOutcomeError("trajectory cost lineage length mismatch")
    stages: dict[str, int] = {}
    unavailable: set[str] = set()
    outer_repairs = 0
    logical_calls = 0
    for ref, attempt in zip(refs, attempts):
        summary = _read_registered(store, ref, registry, "cost_summary", "cost summary")
        event_refs = tuple(ArtifactRef(**item) for item in attempt["attempt_event_refs"])
        rebuilt = reconcile_cost_events(
            store,
            event_refs,
            summary_key=ref.key,
            registry=registry,
        )
        if rebuilt.artifact_ref != ref or rebuilt.payload != summary:
            raise HisCorrectionOutcomeError("cost summary does not rebuild from raw events")
        logical_axis = summary["axes"]["logical_model_calls"]
        repair_axis = summary["axes"]["outer_repair_attempts"]
        if logical_axis["status"] != "measured" or repair_axis["status"] != "measured":
            raise HisCorrectionOutcomeError("logical-call and repair cost axes must be measured")
        logical_calls += logical_axis["value"]
        outer_repairs += repair_axis["value"]
        unavailable.update(name for name, axis in summary["axes"].items() if axis["status"] == "unavailable")
        for event_ref in event_refs:
            event = _read_json(store, event_ref, "attempt cost event")
            if event["event_type"] == "budget_reserved" and event["cost_delta"].get("logical_model_calls") == 1:
                reservation = event["budget_reservation"]
                if reservation["used_after"] > reservation["limit"]:
                    raise HisCorrectionOutcomeError("logical model reservation exceeds its budget")
                stages[event["stage"]] = stages.get(event["stage"], 0) + 1
    allowed = {"req2his", "system_his_repair", "his2project", "project_repair"}
    if (
        set(stages) - allowed or logical_calls != sum(stages.values())
        or stages.get("req2his", 0) not in {0, 1}
        or stages.get("system_his_repair") != 1 or stages.get("his2project") != 1
    ):
        raise HisCorrectionOutcomeError("logical model stages do not reconcile")
    if outer_repairs != stages.get("project_repair", 0):
        raise HisCorrectionOutcomeError("project repair calls do not reconcile with raw costs")
    return {
        "all_axes_classified": True,
        "logical_model_calls": logical_calls,
        "logical_model_stages": stages,
        "his_corrections": 1,
        "extra_his_corrections": 0,
        "project_repairs": outer_repairs,
        "unavailable_axes": sorted(unavailable),
    }


def _expected_initial_statuses(failed_stage: str) -> dict[str, str]:
    index = _H_STAGES.index(failed_stage)
    return {stage: "pass" if i < index else "fail" if i == index else "not_run" for i, stage in enumerate(_H_STAGES)}


def _read_registered(store, ref, registry, key, label):
    payload = _read_json(store, ref, label)
    errors = registry.load_schema(key).validate(payload)
    if errors:
        raise HisCorrectionOutcomeError(f"invalid {label}: " + "; ".join(errors))
    return payload


def _read_json(store, ref, label):
    try:
        payload = json.loads(store.read_verified(ref))
    except json.JSONDecodeError as exc:
        raise HisCorrectionOutcomeError(f"{label} is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise HisCorrectionOutcomeError(f"{label} must be a JSON object")
    return payload


