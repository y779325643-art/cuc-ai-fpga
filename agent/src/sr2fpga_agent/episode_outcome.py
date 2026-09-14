"""Fail-closed development projections and event-derived episode reducers."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from sr2fpga_agent.models import canonical_json_bytes as _canonical_json
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import reconcile_attempt_trajectory
from sr2fpga_agent.evaluator_dispatch import (
    read_verified_development_hidden_conformance_outcome,
)
from sr2fpga_agent.paired_measurement import build_episode_measurement
from sr2fpga_agent.public_evaluator import read_verified_development_public_outcome
from sr2fpga_agent.method_contract import method_policy_sha256


_METHODS = ("M0", "M1", "M2", "M3", "M4", "M5")
_H_METHODS = frozenset({"M3", "M4", "M5"})
_MISSINGNESS_CLASSES = (
    "scoreable_public_record",
    "design_outcome",
    "infrastructure_unscorable",
)


class EpisodeOutcomeError(ValueError):
    pass


@dataclass(frozen=True)
class EpisodeOutcomeRecord:
    method_condition: str
    outcome_ref: ArtifactRef


def project_development_public_evaluation(
    store: ArtifactStore,
    *,
    sample_dir: Path,
    episode_id: str,
    method_condition: str,
    analysis_population: str,
    terminal_public_outcome_ref: ArtifactRef | None = None,
    registry: ContractRegistry | None = None,
) -> tuple[dict[str, Any], ArtifactRef]:
    """Sanitize legacy Recorder output into a closed, non-official projection."""

    if method_condition not in _METHODS:
        raise EpisodeOutcomeError("unknown method condition")
    if analysis_population not in {"development", "excluded"}:
        raise EpisodeOutcomeError("unsupported development analysis population")
    labels_path = Path(sample_dir) / "eval" / "labels.json"
    trajectory_path = Path(sample_dir) / "eval" / "trajectory.json"
    labels_bytes, labels = _read_object_file(labels_path, "legacy labels")
    trajectory_bytes, trajectory = _read_object_file(
        trajectory_path, "legacy trajectory"
    )
    if trajectory.get("sample_id") != episode_id:
        raise EpisodeOutcomeError("legacy trajectory episode identity mismatch")

    measurement = trajectory.get("measurement")
    if not isinstance(measurement, dict):
        raise EpisodeOutcomeError("legacy trajectory measurement is missing")
    repair = _project_repair(trajectory, measurement)
    stages = _project_stages(labels, method_condition)
    source_kind = "legacy_recorder_projection"
    public_authority_status = "legacy_projection_not_official"
    source: dict[str, Any] = {
        "kind": source_kind,
        "labels_sha256": hashlib.sha256(labels_bytes).hexdigest(),
        "trajectory_sha256": hashlib.sha256(trajectory_bytes).hexdigest(),
    }
    if terminal_public_outcome_ref is not None:
        authority_outcome = read_verified_development_public_outcome(
            store, terminal_public_outcome_ref, registry=registry
        )
        if (
            authority_outcome["episode_id"],
            authority_outcome["method_condition"],
        ) != (episode_id, method_condition):
            raise EpisodeOutcomeError("terminal public authority identity mismatch")
        for stage in ("l0", "l1", "public_l2", "l3"):
            stages[stage] = dict(authority_outcome["stage_outcomes"][stage])
        source_kind = "development_terminal_authority_projection"
        public_authority_status = "development_terminal_shadow_not_official"
        source = {
            "kind": source_kind,
            "labels_sha256": hashlib.sha256(labels_bytes).hexdigest(),
            "trajectory_sha256": hashlib.sha256(trajectory_bytes).hexdigest(),
            "authority_outcome_ref": terminal_public_outcome_ref.to_dict(),
        }
    missingness = _classify_missingness(labels, measurement, stages)
    without_id = {
        "contract_version": "development-public-evaluation-v1",
        "evaluation_scope": "development_public_projection_only",
        "episode_id": episode_id,
        "method_condition": method_condition,
        "analysis_population": analysis_population,
        "source": source,
        "public_authority_status": public_authority_status,
        "stage_outcomes": stages,
        "repair": repair,
        "missingness": missingness,
        "official_outcome": False,
        "vpp_l3": None,
    }
    payload = {
        **without_id,
        "projection_id": "public-evaluation-"
        + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
    }
    contract_registry = registry or ContractRegistry()
    reference = store.put_validated_json(
        f"public-evaluations/{episode_id}/{method_condition}",
        payload,
        contract_key="development_public_evaluation",
        registry=contract_registry,
    )
    return payload, reference


def read_verified_development_episode_outcome(
    store: ArtifactStore,
    outcome_ref: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    """Read one episode outcome and rebuild every derived field from its refs."""

    contract_registry = registry or ContractRegistry()
    payload = _read_registered(
        store,
        outcome_ref,
        contract_registry,
        "development_episode_outcome",
        "development episode outcome",
    )
    rebuilt, rebuilt_ref = reconcile_development_episode_outcome(
        store,
        public_evaluation_ref=ArtifactRef(**payload["public_evaluation_ref"]),
        trajectory_ref=ArtifactRef(**payload["trajectory_ref"]),
        registry=contract_registry,
    )
    if rebuilt != payload or rebuilt_ref != outcome_ref:
        raise EpisodeOutcomeError(
            "development episode outcome does not rebuild from source artifacts"
        )
    return payload


def reconcile_development_episode_outcome(
    store: ArtifactStore,
    *,
    public_evaluation_ref: ArtifactRef,
    trajectory_ref: ArtifactRef,
    registry: ContractRegistry | None = None,
) -> tuple[dict[str, Any], ArtifactRef]:
    """Reduce verified public, cost, lineage and opaque-hidden artifacts."""

    contract_registry = registry or ContractRegistry()
    public = _read_registered(
        store,
        public_evaluation_ref,
        contract_registry,
        "development_public_evaluation",
        "development public evaluation",
    )
    trajectory = _read_registered(
        store,
        trajectory_ref,
        contract_registry,
        "trajectory_v2",
        "trajectory-v2",
    )
    identity = (public["episode_id"], public["method_condition"])
    if (trajectory["episode_id"], trajectory["method_condition"]) != identity:
        raise EpisodeOutcomeError("public evaluation and trajectory identity mismatch")
    if public["analysis_population"] != "excluded":
        raise EpisodeOutcomeError("development episode outcome requires excluded input")
    if trajectory["lineage_complete"] is not True:
        raise EpisodeOutcomeError("episode outcome requires complete trajectory lineage")
    terminal_payload = trajectory["terminal_candidate_ref"]
    if not isinstance(terminal_payload, dict):
        raise EpisodeOutcomeError("episode outcome requires a terminal candidate")
    terminal = _read_registered(
        store,
        ArtifactRef(**terminal_payload),
        contract_registry,
        "terminal_candidate",
        "terminal candidate",
    )
    authority = None
    authority_ref_payload = public["source"].get("authority_outcome_ref")
    if authority_ref_payload is not None:
        authority = read_verified_development_public_outcome(
            store,
            ArtifactRef(**authority_ref_payload),
            registry=contract_registry,
        )
        if authority["terminal_candidate_sha256"] != ArtifactRef(**terminal_payload).sha256:
            raise EpisodeOutcomeError("public authority terminal candidate mismatch")
        if authority["public_profile_sha256"] != terminal["requirement_projection_sha256"]:
            raise EpisodeOutcomeError("public authority requirement profile mismatch")
        if authority["public_contract_sha256"] != method_policy_sha256(identity[1]):
            raise EpisodeOutcomeError("public authority method contract mismatch")

    hidden_conformance_ref = _optional_artifact_ref(
        trajectory.get("development_hidden_conformance_outcome_ref")
    )
    hidden_conformance = None
    if hidden_conformance_ref is not None:
        hidden_conformance = read_verified_development_hidden_conformance_outcome(
            store,
            hidden_conformance_ref,
            registry=contract_registry,
        )
        if (
            hidden_conformance["episode_id"],
            hidden_conformance["method_condition"],
        ) != identity:
            raise EpisodeOutcomeError("hidden conformance identity mismatch")
        if hidden_conformance["terminal_candidate_sha256"] != ArtifactRef(
            **terminal_payload
        ).sha256:
            raise EpisodeOutcomeError("hidden conformance terminal candidate mismatch")
        if hidden_conformance["opaque_outcome_ref"] != trajectory[
            "development_hidden_outcome_ref"
        ]:
            raise EpisodeOutcomeError("hidden conformance opaque reference mismatch")
        if hidden_conformance["public_profile_sha256"] != terminal[
            "requirement_projection_sha256"
        ]:
            raise EpisodeOutcomeError("hidden conformance requirement profile mismatch")
        if hidden_conformance["public_contract_sha256"] != method_policy_sha256(
            identity[1]
        ):
            raise EpisodeOutcomeError("hidden conformance method contract mismatch")
        if authority is not None and (
            hidden_conformance["public_contract_sha256"],
            hidden_conformance["public_profile_sha256"],
            hidden_conformance["tool_environment_policy_sha256"],
        ) != (
            authority["public_contract_sha256"],
            authority["public_profile_sha256"],
            authority["tool_environment_policy_sha256"],
        ):
            raise EpisodeOutcomeError("public and hidden conformance commitments disagree")

    summary_refs = [
        ArtifactRef(**attempt["cost_summary_ref"]) for attempt in trajectory["attempts"]
    ]
    rebuilt = reconcile_attempt_trajectory(
        store,
        summary_refs,
        terminal_candidate_ref=ArtifactRef(**terminal_payload),
        development_hidden_outcome_ref=trajectory["development_hidden_outcome_ref"],
        development_hidden_conformance_outcome_ref=_optional_artifact_ref(
            trajectory.get("development_hidden_conformance_outcome_ref")
        ),
        development_terminal_selection_ref=_optional_artifact_ref(
            trajectory.get("development_terminal_selection_ref")
        ),
        development_selected_public_outcome_ref=_optional_artifact_ref(
            trajectory.get("development_selected_public_outcome_ref")
        ),
        development_terminal_public_outcome_ref=_optional_artifact_ref(
            trajectory.get("development_terminal_public_outcome_ref")
        ),
        registry=contract_registry,
    )
    if rebuilt.artifact_ref != trajectory_ref or rebuilt.payload != trajectory:
        raise EpisodeOutcomeError("trajectory does not rebuild from raw attempt events")

    outer_repairs = 0
    hidden_evaluator_calls = 0
    for reference in summary_refs:
        summary = _read_registered(
            store,
            reference,
            contract_registry,
            "cost_summary",
            "cost summary",
        )
        axis = summary["axes"]["outer_repair_attempts"]
        if axis["status"] != "measured" or not isinstance(axis["value"], int):
            raise EpisodeOutcomeError("outer repair cost axis must be measured")
        outer_repairs += axis["value"]
        hidden_axis = summary["axes"]["hidden_evaluator_tool_calls"]
        if hidden_axis["status"] != "measured" or not isinstance(
            hidden_axis["value"], int
        ):
            raise EpisodeOutcomeError(
                "hidden evaluator cost axis must be measured"
            )
        hidden_evaluator_calls += hidden_axis["value"]
    if outer_repairs != public["repair"]["calls_attempted"]:
        raise EpisodeOutcomeError("repair calls do not reconcile with cost events")
    if public["repair"]["reconciliation_status"] != "complete":
        raise EpisodeOutcomeError("repair reconciliation is incomplete")
    if public["repair"]["issues"]:
        raise EpisodeOutcomeError("repair reconciliation contains issues")
    if hidden_conformance is not None:
        if hidden_evaluator_calls != 1:
            raise EpisodeOutcomeError(
                "hidden conformance requires exactly one hidden evaluator call"
            )
        _verify_terminal_hidden_event_sequence(store, trajectory)

    (
        development_vpp_status,
        development_vpp,
        development_vpp_reasons,
    ) = _development_vpp_l3(public["stage_outcomes"], hidden_conformance)

    without_id = {
        "contract_version": "development-episode-outcome-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "episode_id": identity[0],
        "method_condition": identity[1],
        "analysis_population": "excluded",
        "public_evaluation_ref": public_evaluation_ref.to_dict(),
        "trajectory_ref": trajectory_ref.to_dict(),
        "terminal_candidate_ref": terminal_payload,
        "cost_summary_refs": [reference.to_dict() for reference in summary_refs],
        "development_hidden_outcome_ref": trajectory[
            "development_hidden_outcome_ref"
        ],
        "development_hidden_conformance_outcome_ref": (
            hidden_conformance_ref.to_dict()
            if hidden_conformance_ref is not None
            else None
        ),
        "lineage_complete": True,
        "all_cost_axes_classified": True,
        "stage_outcomes": public["stage_outcomes"],
        "repair": public["repair"],
        "missingness": public["missingness"],
        "vpp_l3_status": "not_evaluated",
        "vpp_l3": None,
        "vpp_l3_reasons": [
            "official_hidden_outcome_unavailable",
            "public_authority_not_official",
        ],
        "development_vpp_l3_status": development_vpp_status,
        "development_vpp_l3": development_vpp,
        "development_vpp_l3_reasons": development_vpp_reasons,
        "denominator": {
            "population": "excluded",
            "retained": True,
            "replacement_allowed": False,
        },
        "official_outcome": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
    }
    payload = {
        **without_id,
        "outcome_id": "episode-outcome-"
        + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
    }
    reference = store.put_validated_json(
        f"episode-outcomes/{identity[0]}/{identity[1]}",
        payload,
        contract_key="development_episode_outcome",
        registry=contract_registry,
    )
    return payload, reference


def reconcile_excluded_full_pack_outcomes(
    store: ArtifactStore,
    *,
    smoke_id: str,
    source_runner_reconciliation_ref: ArtifactRef,
    outcomes: Iterable[EpisodeOutcomeRecord],
    registry: ContractRegistry | None = None,
) -> tuple[dict[str, Any], ArtifactRef]:
    """Aggregate exactly one retained, non-official M0-M5 outcome record."""

    contract_registry = registry or ContractRegistry()
    runner = _read_registered(
        store,
        source_runner_reconciliation_ref,
        contract_registry,
        "full_pack_runner_reconciliation_v2",
        "full-pack Runner reconciliation",
    )
    if runner["smoke_id"] != smoke_id or runner["analysis_population"] != "excluded":
        raise EpisodeOutcomeError("full-pack outcome source identity mismatch")
    source_by_method = {
        record["method_condition"]: record for record in runner["method_records"]
    }
    records = tuple(outcomes)
    by_method = {record.method_condition: record for record in records}
    if len(records) != 6 or set(by_method) != set(_METHODS):
        raise EpisodeOutcomeError("full-pack outcomes require exactly one M0-M5 record")

    method_records: list[dict[str, Any]] = []
    repairs = Counter()
    development_vpp_counts = Counter(
        {"evaluated": 0, "pass": 0, "fail": 0, "not_evaluated": 0}
    )
    missingness = Counter({name: 0 for name in _MISSINGNESS_CLASSES})
    for method in _METHODS:
        record = by_method[method]
        outcome = _read_registered(
            store,
            record.outcome_ref,
            contract_registry,
            "development_episode_outcome",
            f"{method} episode outcome",
        )
        source = source_by_method.get(method)
        if source is None:
            raise EpisodeOutcomeError(f"{method} is absent from Runner reconciliation")
        if (
            outcome["method_condition"],
            outcome["episode_id"],
            outcome["trajectory_ref"],
            outcome["terminal_candidate_ref"],
        ) != (
            method,
            source["episode_id"],
            source["trajectory_ref"],
            source["terminal_candidate_ref"],
        ):
            raise EpisodeOutcomeError(f"{method} outcome does not match Runner artifacts")
        if outcome["denominator"] != {
            "population": "excluded",
            "retained": True,
            "replacement_allowed": False,
        }:
            raise EpisodeOutcomeError(f"{method} denominator disposition is invalid")
        if outcome["vpp_l3_status"] != "not_evaluated" or outcome["vpp_l3"] is not None:
            raise EpisodeOutcomeError(f"{method} development VPP must remain not_evaluated")
        development_status = outcome.get(
            "development_vpp_l3_status", "not_evaluated"
        )
        development_value = outcome.get("development_vpp_l3")
        if development_status == "evaluated" and isinstance(development_value, bool):
            development_vpp_counts["evaluated"] += 1
            development_vpp_counts["pass" if development_value else "fail"] += 1
        elif development_status == "not_evaluated" and development_value is None:
            development_vpp_counts["not_evaluated"] += 1
        else:
            raise EpisodeOutcomeError(
                f"{method} development VPP status/value is inconsistent"
            )
        repair = outcome["repair"]
        repairs["calls"] += repair["calls_attempted"]
        repairs["transitions"] += repair["transitions"]
        repairs["successes"] += repair["successes"]
        missingness[outcome["missingness"]["classification"]] += 1
        method_records.append(
            {
                "method_condition": method,
                "episode_id": outcome["episode_id"],
                "outcome_ref": record.outcome_ref.to_dict(),
            }
        )

    payload = {
        "contract_version": "full-pack-outcome-reconciliation-v2",
        "evaluation_scope": "excluded_development_conformance_only",
        "smoke_id": smoke_id,
        "analysis_population": "excluded",
        "g3_accepted": False,
        "g4b_authorized": False,
        "official_outcome": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "source_runner_reconciliation_ref": source_runner_reconciliation_ref.to_dict(),
        "method_records": method_records,
        "summary": {
            "method_set": list(_METHODS),
            "frozen_episode_count": 6,
            "retained_episode_count": 6,
            "replacement_count": 0,
            "vpp_evaluated_count": 0,
            "vpp_pass_count": 0,
            "vpp_fail_count": 0,
            "vpp_not_evaluated_count": 6,
            "development_vpp_evaluated_count": development_vpp_counts["evaluated"],
            "development_vpp_pass_count": development_vpp_counts["pass"],
            "development_vpp_fail_count": development_vpp_counts["fail"],
            "development_vpp_not_evaluated_count": development_vpp_counts[
                "not_evaluated"
            ],
            "repair_calls_attempted": repairs["calls"],
            "repair_transitions": repairs["transitions"],
            "repair_successes": repairs["successes"],
            "missingness_counts": dict(missingness),
        },
        "blocking_gaps": [
            "runtime_scenario_evidence_reconciliation",
            "official_public_terminal_hidden_authority",
            "g4b_campaign_authority",
        ],
    }
    reference = store.put_validated_json(
        f"full-pack-smokes/{smoke_id}/outcome-reconciliation-v2",
        payload,
        contract_key="full_pack_outcome_reconciliation_v2",
        registry=contract_registry,
    )
    return payload, reference


def _development_vpp_l3(
    stage_outcomes: Mapping[str, Any],
    hidden_conformance: Mapping[str, Any] | None,
) -> tuple[str, bool | None, list[str]]:
    if hidden_conformance is None:
        return (
            "not_evaluated",
            None,
            ["development_hidden_conformance_outcome_unavailable"],
        )
    hidden_l2 = hidden_conformance["hidden_l2"]
    required_public = ("l0", "l1", "public_l2", "l3")
    failed = [
        f"{stage}_failed"
        for stage in required_public
        if stage_outcomes[stage]["status"] == "fail"
    ]
    if hidden_l2["status"] == "fail":
        failed.append("hidden_l2_failed")
    if failed:
        return "evaluated", False, failed

    unavailable = [
        f"{stage}_not_run:{stage_outcomes[stage]['reason']}"
        for stage in required_public
        if stage_outcomes[stage]["status"] != "pass"
    ]
    if hidden_l2["status"] == "not_run":
        unavailable.append(f"hidden_l2_not_run:{hidden_l2['reason']}")
    if unavailable:
        return "not_evaluated", None, unavailable
    return "evaluated", True, []


def _verify_terminal_hidden_event_sequence(
    store: ArtifactStore,
    trajectory: Mapping[str, Any],
) -> None:
    """Require hidden evaluation to be the final non-accounting operation."""

    attempts = trajectory["attempts"]
    hidden_events: list[tuple[int, int, list[dict[str, Any]]]] = []
    for attempt_index, attempt in enumerate(attempts):
        events = [
            json.loads(store.read_verified(ArtifactRef(**reference)))
            for reference in attempt["attempt_event_refs"]
        ]
        for event_index, event in enumerate(events):
            if event["stage"] == "development_hidden_evaluator":
                hidden_events.append((attempt_index, event_index, events))
            elif (
                event["event_type"] != "accounting_closed"
                and event["cost_delta"].get("hidden_evaluator_tool_calls", 0) != 0
            ):
                raise EpisodeOutcomeError(
                    "hidden evaluator call is recorded outside its private stage"
                )

    if len(hidden_events) != 1:
        raise EpisodeOutcomeError(
            "hidden conformance requires one raw hidden evaluator event"
        )
    attempt_index, event_index, events = hidden_events[0]
    if attempt_index != len(attempts) - 1:
        raise EpisodeOutcomeError("hidden evaluation must occur on the final attempt")
    event = events[event_index]
    if (
        event["visibility_class"] != "evaluator_private"
        or event["event_type"] != "axis_cost"
        or event["status"] != "completed"
        or event["cost_delta"].get("hidden_evaluator_tool_calls") != 1
        or not isinstance(event["cost_delta"].get("hidden_evaluator_runtime"), (int, float))
    ):
        raise EpisodeOutcomeError("raw hidden evaluator event is not closed")
    for following in events[event_index + 1 :]:
        if following["stage"] not in {"attempt_lifecycle", "accounting_close"}:
            raise EpisodeOutcomeError("non-accounting work occurs after hidden evaluation")
        if (
            following["event_type"] != "accounting_closed"
            and following["cost_delta"].get("outer_repair_attempts", 0) != 0
        ):
            raise EpisodeOutcomeError("repair occurs after hidden evaluation")


def _project_repair(
    trajectory: Mapping[str, Any], measurement: Mapping[str, Any]
) -> dict[str, Any]:
    attempts = trajectory.get("attempt_measurements")
    patches = trajectory.get("patches", [])
    issues: list[str] = []
    rebuilt: Mapping[str, Any] = measurement
    if isinstance(attempts, list) and attempts and isinstance(patches, list):
        rebuilt = build_episode_measurement(
            attempts=attempts,
            patches=patches,
            l4_open=measurement.get("l4_open"),
        )
        if dict(rebuilt) != dict(measurement):
            raise EpisodeOutcomeError("legacy repair measurement does not rebuild")
    else:
        issues.append("attempt_measurements_unavailable")
    accounting = rebuilt.get("repair_accounting")
    if not isinstance(accounting, dict):
        raise EpisodeOutcomeError("legacy repair accounting is missing")
    accounting_issues = accounting.get("issues", [])
    if not isinstance(accounting_issues, list):
        raise EpisodeOutcomeError("legacy repair accounting issues are invalid")
    issues.extend(str(issue) for issue in accounting_issues if str(issue))
    calls = _nonnegative_int(accounting.get("repair_calls_attempted"), "repair calls")
    transitions = _nonnegative_int(accounting.get("repair_transitions"), "repair transitions")
    successes = int(bool(rebuilt.get("repair_success")))
    if not (successes <= transitions <= calls):
        raise EpisodeOutcomeError("repair accounting totals are inconsistent")
    by_scope_raw = accounting.get("by_scope")
    if not isinstance(by_scope_raw, dict):
        raise EpisodeOutcomeError("repair scope accounting is missing")
    by_scope: dict[str, Any] = {}
    for scope in ("system_his", "project"):
        raw = by_scope_raw.get(scope)
        if not isinstance(raw, dict):
            raise EpisodeOutcomeError(f"repair scope {scope} is missing")
        by_scope[scope] = {
            "calls_attempted": _nonnegative_int(
                raw.get("calls_attempted"), f"{scope} repair calls"
            ),
            "transitions": _nonnegative_int(
                raw.get("transitions"), f"{scope} repair transitions"
            ),
        }
    diagnoses = sum(
        int(
            isinstance(item, dict)
            and item.get("repair_attempted") is True
            and str(item.get("failure_type", "none")) != "none"
        )
        for item in (attempts if isinstance(attempts, list) else [])
    )
    valid_patches = sum(
        int(isinstance(item, dict) and item.get("status") == "valid")
        for item in (patches if isinstance(patches, list) else [])
    )
    return {
        "reconciliation_status": "complete" if not issues else "incomplete",
        "calls_attempted": calls,
        "transitions": transitions,
        "successes": successes,
        "diagnosis_count": diagnoses,
        "valid_patch_count": valid_patches,
        "rerun_count": transitions,
        "by_scope": by_scope,
        "issues": sorted(set(issues)),
    }


def _project_stages(labels: Mapping[str, Any], method: str) -> dict[str, Any]:
    checks = labels.get("checks")
    if not isinstance(checks, dict):
        raise EpisodeOutcomeError("legacy labels checks are missing")
    pass_level = str(labels.get("pass_level", "GEN_FAIL"))
    failure_type = str(labels.get("failure_type", ""))
    generation_failed = pass_level == "GEN_FAIL" or failure_type == "generation_failed"
    stages: dict[str, Any] = {
        "generation": _stage("fail" if generation_failed else "pass", failure_type or None),
    }
    for name in ("h0", "h1", "h2", "h3"):
        if method not in _H_METHODS:
            stages[name] = _stage("not_applicable", "method_does_not_emit_system_his")
        else:
            stages[name] = _stage_from_text(
                labels.get(f"{name}_status"), f"{name}_status_unavailable"
            )
    stages["l0"] = _stage_from_check(
        checks.get("l0_complete"),
        upstream_failed=generation_failed or any(
            stages[name]["status"] == "fail" for name in ("h0", "h1", "h2", "h3")
        ),
        missing_reason="l0_status_unavailable",
    )
    stages["l1"] = _stage_from_check(
        checks.get("l1_lint_pass"),
        upstream_failed=stages["l0"]["status"] != "pass",
        missing_reason="l1_status_unavailable",
    )
    stages["public_l2"] = _stage_from_text(
        labels.get("l2_sim_status"),
        str(labels.get("l2_sim_skip_reason") or "public_l2_status_unavailable"),
    )
    stages["l3"] = _stage_from_check(
        checks.get("l3_synth_pass"),
        upstream_failed=stages["l1"]["status"] != "pass",
        missing_reason="l3_status_unavailable",
    )
    return stages


def _classify_missingness(
    labels: Mapping[str, Any],
    measurement: Mapping[str, Any],
    stages: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    infrastructure_status = str(measurement.get("infrastructure_status", "scoreable"))
    if measurement.get("scoreable") is not True or infrastructure_status != "scoreable":
        classification = "infrastructure_unscorable"
        reason: str | None = infrastructure_status
    elif stages["public_l2"]["status"] == "not_run":
        classification = "infrastructure_unscorable"
        reason = "public_l2:" + str(stages["public_l2"]["reason"])
    elif any(stage["status"] == "fail" for stage in stages.values()):
        classification = "design_outcome"
        reason = str(labels.get("failure_type") or "public_stage_failure")
    else:
        classification = "scoreable_public_record"
        reason = None
    return {
        "classification": classification,
        "reason": reason,
        "retained": True,
        "replacement_allowed": False,
    }


def _stage_from_text(value: Any, missing_reason: str) -> dict[str, Any]:
    normalized = {"passed": "pass", "failed": "fail"}.get(str(value), str(value))
    if normalized in {"pass", "fail", "not_applicable"}:
        return _stage(normalized, None)
    if normalized == "not_run":
        return _stage("not_run", missing_reason)
    return _stage("not_run", missing_reason)


def _stage_from_check(
    value: Any, *, upstream_failed: bool, missing_reason: str
) -> dict[str, Any]:
    if value is True:
        return _stage("pass", None)
    if value is False:
        return _stage(
            "not_run" if upstream_failed else "fail",
            "upstream_stage_not_pass" if upstream_failed else None,
        )
    return _stage("not_run", missing_reason)


def _stage(status: str, reason: str | None) -> dict[str, Any]:
    if status in {"pass", "fail", "not_applicable"}:
        reason = reason if status == "fail" and reason else None
    return {"status": status, "reason": reason}


def _read_object_file(path: Path, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        content = path.read_bytes()
        payload = json.loads(content)
    except OSError as exc:
        raise EpisodeOutcomeError(f"{label} is unavailable") from exc
    except json.JSONDecodeError as exc:
        raise EpisodeOutcomeError(f"{label} is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise EpisodeOutcomeError(f"{label} must be an object")
    return content, payload


def _read_registered(
    store: ArtifactStore,
    reference: ArtifactRef,
    registry: ContractRegistry,
    contract_key: str,
    label: str,
) -> dict[str, Any]:
    try:
        payload = json.loads(store.read_verified(reference))
    except json.JSONDecodeError as exc:
        raise EpisodeOutcomeError(f"{label} is not valid JSON") from exc
    errors = registry.load_schema(contract_key).validate(payload)
    if errors:
        raise EpisodeOutcomeError(f"invalid {label}: " + "; ".join(errors))
    _verify_content_id(payload, contract_key, label)
    return payload


def _verify_content_id(
    payload: Mapping[str, Any], contract_key: str, label: str
) -> None:
    identity = {
        "development_public_evaluation": ("projection_id", "public-evaluation-"),
        "development_episode_outcome": ("outcome_id", "episode-outcome-"),
    }.get(contract_key)
    if identity is None:
        return
    field, prefix = identity
    without_id = {key: value for key, value in payload.items() if key != field}
    expected = prefix + hashlib.sha256(_canonical_json(without_id)).hexdigest()
    if payload.get(field) != expected:
        raise EpisodeOutcomeError(f"{label} content-derived ID mismatch")


def _nonnegative_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EpisodeOutcomeError(f"{label} must be a non-negative integer")
    return value


def _optional_artifact_ref(payload: Any) -> ArtifactRef | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise EpisodeOutcomeError("trajectory authority reference is invalid")
    try:
        return ArtifactRef(**payload)
    except TypeError as exc:
        raise EpisodeOutcomeError("trajectory authority reference is invalid") from exc


