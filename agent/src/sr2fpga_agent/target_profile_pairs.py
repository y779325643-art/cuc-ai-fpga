"""Development-only target-profile pair contracts and reconciliation."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry


PILOT_PAIR_MANIFEST_VERSION = "pilot-target-profile-pair-manifest-v1"
DEVELOPMENT_PAIR_OUTCOME_VERSION = "development-target-profile-pair-outcome-v1"

_MEMBER_ROLES = ("baseline", "variant")
_COST_AXES = (
    "logical_model_calls",
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "provider_transport_attempts",
    "planner_parser_schema_retries",
    "outer_repair_attempts",
    "public_tool_calls",
    "hidden_evaluator_tool_calls",
    "hidden_infrastructure_retries",
    "wall_time",
    "eda_time",
    "hidden_evaluator_runtime",
)
_OBSERVATION_KEYS = {
    "member_role",
    "profile_member_id",
    "target_profile_id",
    "target_profile_sha256",
    "execution_status",
    "candidate_ref",
    "invariant_status",
    "required_changes_status",
    "forbidden_changes_status",
    "profile_compliance_status",
    "l3_status",
    "l4_status",
    "violation_ids",
    "cost_summary_ref",
}


def build_pilot_target_profile_pair_manifest(
    manifest_id: str,
    protocol_sha256: str,
    pairs: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    pair_records = [dict(pair) for pair in pairs]
    payload = {
        "contract_version": PILOT_PAIR_MANIFEST_VERSION,
        "manifest_id": manifest_id,
        "protocol_sha256": protocol_sha256,
        "population_role": "pilot_only_excluded",
        "visibility_class": "evaluator_only",
        "profile_pair_count": len(pair_records),
        "pairs": pair_records,
        "official_population": False,
        "g4b_authorized": False,
        "pass_credit_authority": False,
        "official_authority": False,
    }
    artifact = {**payload, "artifact_sha256": _sha256(payload)}
    validate_pilot_target_profile_pair_manifest(artifact)
    return artifact


def validate_pilot_target_profile_pair_manifest(artifact: Mapping[str, Any]) -> None:
    payload = dict(artifact)
    errors = ContractRegistry().load_schema("pilot_target_profile_pair_manifest").validate(
        payload
    )
    if errors:
        raise ValueError("invalid pilot target-profile pair manifest: " + "; ".join(errors))
    expected_sha = _sha256({key: value for key, value in payload.items() if key != "artifact_sha256"})
    if payload["artifact_sha256"] != expected_sha:
        raise ValueError("pilot target-profile pair manifest SHA-256 mismatch")
    pairs = payload["pairs"]
    if payload["profile_pair_count"] != len(pairs):
        raise ValueError("profile_pair_count does not match pairs")
    _require_unique((pair["profile_pair_id"] for pair in pairs), "profile_pair_id")
    _require_unique(
        (
            member["profile_member_id"]
            for pair in pairs
            for member in pair["members"]
        ),
        "profile_member_id",
    )
    for pair in pairs:
        _validate_pair_rules(pair)


def build_development_target_profile_pair_outcome(
    manifest: Mapping[str, Any],
    profile_pair_id: str,
    method_condition: str,
    member_observations: Iterable[Mapping[str, Any]],
    *,
    store: ArtifactStore,
) -> dict[str, Any]:
    validate_pilot_target_profile_pair_manifest(manifest)
    pair = _pair_by_id(manifest, profile_pair_id)
    observations = [dict(item) for item in member_observations]
    _require_exact_observation_keys(observations)
    by_role = _records_by_role(observations, "member observations")
    member_records: list[dict[str, Any]] = []
    cost_refs: list[dict[str, Any]] = []
    member_axes: list[dict[str, Any]] = []
    for expected in pair["members"]:
        role = expected["member_role"]
        observation = by_role[role]
        _validate_member_identity(expected, observation)
        _validate_observation_semantics(observation)
        candidate_ref = _validated_optional_ref(
            store, observation["candidate_ref"], f"{role} candidate"
        )
        if observation["execution_status"] == "completed" and candidate_ref is None:
            raise ValueError(f"completed {role} member requires candidate_ref")
        cost_ref, axes = _validated_cost_summary(
            store,
            observation["cost_summary_ref"],
            method_condition=method_condition,
            label=f"{role} cost summary",
        )
        if cost_ref is not None:
            cost_refs.append(cost_ref)
        member_axes.append(axes)
        member_records.append(
            {
                **{key: observation[key] for key in _OBSERVATION_KEYS if key != "cost_summary_ref"},
                "candidate_ref": candidate_ref,
                "cost_summary_ref": cost_ref,
                "cost_axes": axes,
            }
        )

    paired_axes = _aggregate_cost_axes(member_axes)
    paired_cost_complete = len(cost_refs) == 2 and all(
        axis["status"] == "measured" for axis in paired_axes.values()
    )
    reasons = _tpa_l4_reasons(member_records, paired_cost_complete)
    any_execution_missing = any(
        record["execution_status"] != "completed" for record in member_records
    )
    any_stage_not_run = any(
        record[field] == "not_run"
        for record in member_records
        for field in (
            "invariant_status",
            "required_changes_status",
            "forbidden_changes_status",
            "profile_compliance_status",
            "l3_status",
            "l4_status",
        )
    )
    pair_complete = not any_execution_missing and paired_cost_complete
    if any_execution_missing or any_stage_not_run or not paired_cost_complete:
        tpa_status = "not_run"
    elif reasons:
        tpa_status = "fail"
    else:
        tpa_status = "pass"
    payload = {
        "contract_version": DEVELOPMENT_PAIR_OUTCOME_VERSION,
        "outcome_id": "development-target-profile-pair-"
        + _sha256(
            {
                "manifest_sha256": manifest["artifact_sha256"],
                "profile_pair_id": profile_pair_id,
                "method_condition": method_condition,
                "members": member_records,
            }
        )[:24],
        "manifest_id": manifest["manifest_id"],
        "manifest_sha256": manifest["artifact_sha256"],
        "profile_pair_id": profile_pair_id,
        "method_condition": method_condition,
        "population_role": "pilot_only_excluded",
        "members": member_records,
        "pair_completeness": "complete" if pair_complete else "incomplete",
        "tpa_l4_status": tpa_status,
        "tpa_l4_reasons": reasons,
        "paired_cost": {
            "status": "complete" if paired_cost_complete else "incomplete",
            "member_cost_summary_refs": cost_refs,
            "axes": paired_axes,
        },
        "terminal_binding": False,
        "pass_credit_authority": False,
        "official_authority": False,
    }
    artifact = {**payload, "artifact_sha256": _sha256(payload)}
    validate_development_target_profile_pair_outcome(artifact, manifest=manifest)
    return artifact


def validate_development_target_profile_pair_outcome(
    artifact: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
) -> None:
    payload = dict(artifact)
    errors = ContractRegistry().load_schema(
        "development_target_profile_pair_outcome"
    ).validate(payload)
    if errors:
        raise ValueError(
            "invalid development target-profile pair outcome: " + "; ".join(errors)
        )
    expected_sha = _sha256({key: value for key, value in payload.items() if key != "artifact_sha256"})
    if payload["artifact_sha256"] != expected_sha:
        raise ValueError("development target-profile pair outcome SHA-256 mismatch")
    by_role = _records_by_role(payload["members"], "outcome members")
    _validate_outcome_reconciliation(payload)
    if manifest is None:
        return
    validate_pilot_target_profile_pair_manifest(manifest)
    if (
        payload["manifest_id"] != manifest["manifest_id"]
        or payload["manifest_sha256"] != manifest["artifact_sha256"]
    ):
        raise ValueError("target-profile pair outcome does not match manifest")
    pair = _pair_by_id(manifest, payload["profile_pair_id"])
    for expected in pair["members"]:
        _validate_member_identity(expected, by_role[expected["member_role"]])


def _validate_pair_rules(pair: Mapping[str, Any]) -> None:
    members = _records_by_role(pair["members"], f"pair {pair['profile_pair_id']} members")
    baseline = members["baseline"]
    variant = members["variant"]
    if baseline["target_profile_id"] == variant["target_profile_id"]:
        raise ValueError("baseline and variant target_profile_id must differ")
    if baseline["target_profile_sha256"] == variant["target_profile_sha256"]:
        raise ValueError("baseline and variant target profile hashes must differ")
    required = set(pair["required_change_ids"])
    allowed = set(pair["allowed_change_ids"])
    forbidden = set(pair["forbidden_change_ids"])
    if not required.issubset(allowed):
        raise ValueError("required changes must be a subset of allowed changes")
    if allowed.intersection(forbidden):
        raise ValueError("allowed and forbidden changes must be disjoint")
    axes = set(pair["change_axes"])
    if "compound_profile" in axes and len(axes) != 1:
        raise ValueError("compound_profile cannot be combined with individual change axes")
    if len(axes) > 1:
        raise ValueError("multiple change axes require one explicit compound_profile")
    if "official_target_profile_population" not in pair["objective_exclusion_ids"]:
        raise ValueError("pilot pair must exclude the official target-profile population")


def _validate_observation_semantics(observation: Mapping[str, Any]) -> None:
    stage_fields = (
        "invariant_status",
        "required_changes_status",
        "forbidden_changes_status",
        "profile_compliance_status",
        "l3_status",
        "l4_status",
    )
    if observation["execution_status"] != "completed" and any(
        observation[field] != "not_run" for field in stage_fields
    ):
        raise ValueError("non-completed member must keep all evaluation stages not_run")
    failed_compliance = any(
        observation[field] == "fail"
        for field in (
            "invariant_status",
            "required_changes_status",
            "forbidden_changes_status",
            "profile_compliance_status",
        )
    )
    if failed_compliance and not observation["violation_ids"]:
        raise ValueError("failed profile compliance requires at least one violation_id")
    if not failed_compliance and observation["violation_ids"]:
        raise ValueError("violation_ids require a failed profile-compliance check")
    if observation["l4_status"] == "pass" and observation["l3_status"] != "pass":
        raise ValueError("L4 pass requires L3 pass for the same profile member")


def _validate_outcome_reconciliation(payload: Mapping[str, Any]) -> None:
    members = list(payload["members"])
    for member in members:
        _validate_observation_semantics(member)
    expected_refs = [
        member["cost_summary_ref"]
        for member in members
        if member["cost_summary_ref"] is not None
    ]
    paired_cost = payload["paired_cost"]
    if paired_cost["member_cost_summary_refs"] != expected_refs:
        raise ValueError("paired cost references do not match member cost summaries")
    expected_axes = _aggregate_cost_axes([dict(member["cost_axes"]) for member in members])
    if paired_cost["axes"] != expected_axes:
        raise ValueError("paired cost axes do not match member-axis reconciliation")
    expected_cost_complete = len(expected_refs) == 2 and all(
        axis["status"] == "measured" for axis in expected_axes.values()
    )
    expected_cost_status = "complete" if expected_cost_complete else "incomplete"
    if paired_cost["status"] != expected_cost_status:
        raise ValueError("paired cost status does not match reconciled axes")
    expected_reasons = _tpa_l4_reasons(members, expected_cost_complete)
    if payload["tpa_l4_reasons"] != expected_reasons:
        raise ValueError("TPA-L4 reasons do not match member outcomes")
    any_execution_missing = any(
        member["execution_status"] != "completed" for member in members
    )
    any_stage_not_run = any(
        member[field] == "not_run"
        for member in members
        for field in (
            "invariant_status",
            "required_changes_status",
            "forbidden_changes_status",
            "profile_compliance_status",
            "l3_status",
            "l4_status",
        )
    )
    expected_completeness = (
        "complete"
        if not any_execution_missing and expected_cost_complete
        else "incomplete"
    )
    if payload["pair_completeness"] != expected_completeness:
        raise ValueError("pair completeness does not match member outcomes and cost")
    if any_execution_missing or any_stage_not_run or not expected_cost_complete:
        expected_tpa = "not_run"
    elif expected_reasons:
        expected_tpa = "fail"
    else:
        expected_tpa = "pass"
    if payload["tpa_l4_status"] != expected_tpa:
        raise ValueError("TPA-L4 status does not match member outcomes")
    expected_outcome_id = "development-target-profile-pair-" + _sha256(
        {
            "manifest_sha256": payload["manifest_sha256"],
            "profile_pair_id": payload["profile_pair_id"],
            "method_condition": payload["method_condition"],
            "members": members,
        }
    )[:24]
    if payload["outcome_id"] != expected_outcome_id:
        raise ValueError("development target-profile pair outcome ID mismatch")


def _validated_cost_summary(
    store: ArtifactStore,
    raw_ref: Any,
    *,
    method_condition: str,
    label: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if raw_ref is None:
        return None, _unavailable_axes("cost_summary_missing")
    reference = _artifact_ref(raw_ref, label)
    try:
        summary = json.loads(store.read_verified(reference))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON") from exc
    errors = ContractRegistry().load_schema("cost_summary").validate(summary)
    if errors:
        raise ValueError(f"invalid {label}: " + "; ".join(errors))
    if summary["method_condition"] != method_condition:
        raise ValueError(f"{label} method_condition mismatch")
    return reference.to_dict(), dict(summary["axes"])


def _validated_optional_ref(
    store: ArtifactStore, raw_ref: Any, label: str
) -> dict[str, Any] | None:
    if raw_ref is None:
        return None
    reference = _artifact_ref(raw_ref, label)
    store.read_verified(reference)
    return reference.to_dict()


def _artifact_ref(raw_ref: Any, label: str) -> ArtifactRef:
    if not isinstance(raw_ref, Mapping):
        raise ValueError(f"{label} reference must be an object")
    try:
        return ArtifactRef(
            key=str(raw_ref["key"]),
            sha256=str(raw_ref["sha256"]),
            size_bytes=int(raw_ref["size_bytes"]),
            media_type=str(raw_ref["media_type"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid {label} reference") from exc


def _aggregate_cost_axes(member_axes: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in _COST_AXES:
        values = [axes[name] for axes in member_axes]
        if len(values) == 2 and all(item["status"] == "measured" for item in values):
            result[name] = {
                "status": "measured",
                "value": sum(float(item["value"]) for item in values),
                "reason": None,
            }
        else:
            result[name] = {
                "status": "unavailable",
                "value": None,
                "reason": "member_axis_unavailable",
            }
    return result


def _unavailable_axes(reason: str) -> dict[str, Any]:
    return {
        name: {"status": "unavailable", "value": None, "reason": reason}
        for name in _COST_AXES
    }


def _tpa_l4_reasons(
    member_records: list[dict[str, Any]], paired_cost_complete: bool
) -> list[str]:
    reasons: set[str] = set()
    for record in member_records:
        if record["execution_status"] == "not_run":
            reasons.add("member_not_run")
        elif record["execution_status"] == "infrastructure_error":
            reasons.add("member_infrastructure_error")
        if any(
            record[field] == "not_run"
            for field in (
                "invariant_status",
                "required_changes_status",
                "forbidden_changes_status",
                "profile_compliance_status",
                "l3_status",
                "l4_status",
            )
        ):
            reasons.add("member_evaluation_not_run")
        if record["invariant_status"] == "fail":
            reasons.add("invariant_failure")
        if record["required_changes_status"] == "fail":
            reasons.add("required_change_failure")
        if record["forbidden_changes_status"] == "fail":
            reasons.add("forbidden_change_detected")
        if record["profile_compliance_status"] == "fail":
            reasons.add("profile_compliance_failure")
        if record["l3_status"] == "fail":
            reasons.add("l3_failure")
        if record["l4_status"] == "fail":
            reasons.add("l4_failure")
    if not paired_cost_complete:
        reasons.add("paired_cost_incomplete")
    return sorted(reasons)


def _require_exact_observation_keys(observations: list[dict[str, Any]]) -> None:
    if len(observations) != 2:
        raise ValueError("target-profile pair outcome requires exactly two member observations")
    for observation in observations:
        keys = set(observation)
        if keys != _OBSERVATION_KEYS:
            missing = sorted(_OBSERVATION_KEYS - keys)
            extra = sorted(keys - _OBSERVATION_KEYS)
            raise ValueError(
                f"member observation fields mismatch; missing={missing}, extra={extra}"
            )


def _records_by_role(records: Iterable[Mapping[str, Any]], label: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        role = str(record.get("member_role", ""))
        if role in result:
            raise ValueError(f"duplicate member_role in {label}: {role}")
        result[role] = record
    if set(result) != set(_MEMBER_ROLES):
        raise ValueError(f"{label} must contain exactly baseline and variant")
    return result


def _validate_member_identity(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> None:
    for field in (
        "member_role",
        "profile_member_id",
        "target_profile_id",
        "target_profile_sha256",
    ):
        if actual.get(field) != expected[field]:
            raise ValueError(f"target-profile member {field} mismatch")


def _pair_by_id(manifest: Mapping[str, Any], profile_pair_id: str) -> Mapping[str, Any]:
    matches = [pair for pair in manifest["pairs"] if pair["profile_pair_id"] == profile_pair_id]
    if len(matches) != 1:
        raise ValueError(f"unknown profile_pair_id: {profile_pair_id}")
    return matches[0]


def _require_unique(values: Iterable[str], label: str) -> None:
    items = list(values)
    if len(items) != len(set(items)):
        raise ValueError(f"duplicate {label}")


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
