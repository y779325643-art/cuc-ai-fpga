"""Offline, stop-before-generation ambiguity audit artifacts for Paper-1 RQ0."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.requirement_boundary import (
    REQUIREMENT_BOUNDARY_VERSION,
    evaluate_requirement_boundary,
)
from sr2fpga_agent.requirement_envelope import effective_request_requirement


REQUIREMENT_AUDIT_VERSION = "requirement-audit-v1"


@dataclass(frozen=True)
class ClarificationAnswerBranch:
    branch_id: str
    answer_facts: dict[str, Any]
    expected_replay_disposition: str


@dataclass(frozen=True)
class RequirementAuditGold:
    disposition: str
    reason_ids: tuple[str, ...] = ()
    fact_ids: tuple[str, ...] = ()
    capability_ids: tuple[str, ...] = ()
    clarification_answer_branches: tuple[ClarificationAnswerBranch, ...] = ()


def build_requirement_audit_case(
    request: ProjectRequest,
    platform: PlatformProfile,
    *,
    base_requirement_cluster_id: str,
    ambiguity_case_id: str,
    gold: RequirementAuditGold,
) -> dict[str, Any]:
    """Evaluate one sealed case without invoking a generator or writing a candidate."""

    if not request.description.strip():
        raise ValueError("sealed requirement-audit cases require explicit public requirement text")
    # A_req is evaluated before method/family assignment.  The task_type carried
    # by project-generation code is evaluator metadata and must not resolve a
    # gold ambiguity.  Any family words genuinely supplied by the user remain
    # in description and are handled only as ordinary public text.
    audit_request = replace(request, task_type="unclassified")
    started = time.monotonic()
    boundary = evaluate_requirement_boundary(audit_request, platform)
    elapsed_ms = (time.monotonic() - started) * 1000.0
    public_requirement = effective_request_requirement(audit_request)
    route_payload = boundary.route.to_dict()

    case = {
        "base_requirement_cluster_id": base_requirement_cluster_id,
        "ambiguity_case_id": ambiguity_case_id,
        "generation_visible_projection": {
            "visibility_class": "generation_visible",
            "public_requirement": public_requirement,
            "public_requirement_sha256": _sha256(public_requirement),
            "width_bits": audit_request.width,
            "platform_profile_id": platform.name,
            "platform_profile_sha256": _sha256(asdict(platform)),
            "capability_profile_id": boundary.capability_profile_id,
            "capability_profile_sha256": boundary.capability_profile_sha256,
        },
        "preflight_projection": {
            "visibility_class": "audit_only",
            "envelope": {
                "envelope_version": boundary.envelope_version,
                "envelope_sha256": boundary.envelope_sha256,
                "requirement_id": boundary.requirement_id,
                "facts": [_fact_record(item) for item in boundary.envelope.facts],
                "ambiguity_fact_ids": list(boundary.clarification_fact_ids),
                "capability_ids": list(boundary.envelope.capability_labels),
            },
            "route": {
                "route_version": REQUIREMENT_BOUNDARY_VERSION,
                "route_sha256": _sha256(route_payload),
                "strategy_id": boundary.route.strategy,
                "reason_ids": list(boundary.reason_codes),
                "fact_ids": list(boundary.clarification_fact_ids),
                "capability_ids": list(boundary.capability_gap_ids),
            },
        },
        "boundary_result": {
            "visibility_class": "audit_only",
            "execution_status": "completed",
            "predicted_disposition": boundary.disposition,
            "reason_ids": list(boundary.reason_codes),
            "fact_ids": list(boundary.clarification_fact_ids),
            "capability_ids": list(boundary.capability_gap_ids),
            "generation_boundary_crossed": False,
            "counters": {
                "model_calls": 0,
                "tool_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "wall_time_ms": elapsed_ms,
            },
        },
        "evaluator_only": _gold_projection(gold),
    }
    return case


def build_requirement_audit_artifact(
    audit_run_id: str,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    if not cases:
        raise ValueError("requirement audit needs at least one case")
    payload = {
        "audit_version": REQUIREMENT_AUDIT_VERSION,
        "audit_run_id": audit_run_id,
        "visibility_class": "evaluator_only",
        "cases": cases,
        "summary": _summarize(cases),
    }
    artifact = {**payload, "audit_sha256": _sha256(payload)}
    validate_requirement_audit_artifact(artifact)
    return artifact


def load_requirement_audit_manifest(path: Path | str) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise ValueError(f"requirement audit manifest does not exist: {manifest_path}")
    if not manifest_path.is_file():
        raise ValueError(f"requirement audit manifest path is not a file: {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"requirement audit manifest at {manifest_path} is not valid JSON: {error}"
        ) from error
    except OSError as error:
        raise ValueError(f"requirement audit manifest at {manifest_path} is not readable: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"requirement audit manifest at {manifest_path} must be a JSON object")
    try:
        validate_requirement_audit_artifact(payload)
    except Exception as error:  # noqa: BLE001
        raise ValueError(
            f"requirement audit manifest at {manifest_path} is not a valid requirement-audit artifact: {error}"
        ) from error
    return payload


def validate_requirement_audit_artifact(artifact: dict[str, Any]) -> None:
    paths = RepositoryPaths.discover()
    schema_path = paths.contracts_dir / "requirement-audit" / "requirement-audit-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(artifact)
    expected = _sha256({key: value for key, value in artifact.items() if key != "audit_sha256"})
    if artifact.get("audit_sha256") != expected:
        raise ValueError("requirement audit SHA-256 does not match its canonical payload")


def write_requirement_audit_artifact(path: Path, artifact: dict[str, Any]) -> None:
    validate_requirement_audit_artifact(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _fact_record(fact: Any) -> dict[str, Any]:
    origins = {
        "explicit": "user_explicit",
        "default": "platform_default",
        "assumption": "system_assumption",
        "unknown": "unresolved",
    }
    return {
        "fact_id": fact.key,
        "origin": origins[fact.origin],
        "value": _json_value(fact.value),
    }


def _gold_projection(gold: RequirementAuditGold) -> dict[str, Any]:
    if gold.disposition not in {"ready", "needs_clarification", "capability_gap"}:
        raise ValueError(f"unsupported gold disposition: {gold.disposition}")
    payload: dict[str, Any] = {
        "visibility_class": "evaluator_only",
        "gold_disposition": gold.disposition,
        "gold_reason_ids": list(gold.reason_ids),
        "gold_fact_ids": list(gold.fact_ids),
        "gold_capability_ids": list(gold.capability_ids),
    }
    if gold.clarification_answer_branches:
        payload["clarification_answer_branches"] = [
            {
                "branch_id": item.branch_id,
                "visibility_class": "evaluator_only",
                "answer_sha256": _sha256(item.answer_facts),
                "answer_facts": _json_value(item.answer_facts),
                "expected_replay_disposition": item.expected_replay_disposition,
            }
            for item in gold.clarification_answer_branches
        ]
    return payload


def _summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    predicted = _disposition_counts(
        case["boundary_result"]["predicted_disposition"]
        for case in cases
        if case["boundary_result"]["execution_status"] == "completed"
    )
    gold = _disposition_counts(case["evaluator_only"]["gold_disposition"] for case in cases)
    execution = {"completed": 0, "not_run": 0}
    confusion = {
        expected: _disposition_counts(())
        for expected in ("ready", "needs_clarification", "capability_gap")
    }
    totals = {
        "model_calls": 0,
        "tool_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "wall_time_ms": 0.0,
    }
    crossed = 0
    false_proceed = 0
    false_block = 0
    for case in cases:
        result = case["boundary_result"]
        expected = case["evaluator_only"]["gold_disposition"]
        actual = result.get("predicted_disposition")
        execution[result["execution_status"]] += 1
        boundary_crossed = bool(result["generation_boundary_crossed"])
        crossed += int(boundary_crossed)
        if result["execution_status"] == "completed":
            if actual in confusion[expected]:
                confusion[expected][actual] += 1
            false_proceed += int(
                expected != "ready" and (actual == "ready" or boundary_crossed)
            )
            false_block += int(expected == "ready" and actual != "ready")
        for key, value in result["counters"].items():
            totals[key] += value
    return {
        "visibility_class": "evaluator_only",
        "case_count": len(cases),
        "execution_status_counts": execution,
        "predicted_disposition_counts": predicted,
        "gold_disposition_counts": gold,
        "confusion_matrix": confusion,
        "generation_boundary_crossed_count": crossed,
        "false_proceed_count": false_proceed,
        "false_block_count": false_block,
        "counter_totals": totals,
    }


def _disposition_counts(values: Any) -> dict[str, int]:
    counts = {"ready": 0, "needs_clarification": 0, "capability_gap": 0}
    for value in values:
        counts[str(value)] += 1
    return counts


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _sha256(value: Any) -> str:
    if isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
