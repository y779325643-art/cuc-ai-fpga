"""Evaluator-owned eligibility certificates for CD8 candidate training pools."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.frozen_context import validate_episode_pack
from sr2fpga_agent.project_contract import validate_project_envelope


TRAINING_ELIGIBILITY_VERSION = "training-eligibility-v1"
_HARD_EXCLUDED_SOURCE_CLASSES = frozenset(
    {"b_ref", "b_template", "reference_deterministic", "deterministic_template"}
)
_HARD_EXCLUDED_FAILURE_ORIGINS = frozenset(
    {"reference_deterministic", "deterministic_template"}
)
_CHECK_REASON_IDS = {
    "training_split_member": "not_in_frozen_training_split",
    "requirement_ready": "requirement_not_ready",
    "initial_snapshot_serializable": "initial_snapshot_not_serializable",
    "initial_snapshot_pre_feedback": "initial_snapshot_not_pre_feedback",
    "qualification_completed_pass": "training_qualification_not_completed_pass",
    "trusted_edit_surface_intact": "trusted_edit_surface_changed",
    "method_applicable_h_pass": "method_applicable_h_not_passed",
    "provenance_complete": "provenance_incomplete",
    "budget_compliant": "budget_not_compliant",
    "hidden_material_redacted": "hidden_material_not_redacted",
    "leakage_audit_pass": "leakage_audit_failed",
    "source_policy_allowed": "source_policy_disallowed",
}


@dataclass(frozen=True)
class TrainingEligibilityPolicy:
    policy_id: str
    policy_sha256: str
    training_split_id: str
    episode_ids: tuple[str, ...]
    allowed_source_classes: tuple[str, ...]
    allowed_failure_origins: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        training_split_id: str,
        episode_ids: tuple[str, ...],
        allowed_source_classes: tuple[str, ...],
        allowed_failure_origins: tuple[str, ...],
    ) -> "TrainingEligibilityPolicy":
        payload = {
            "policy_id": policy_id,
            "training_split_id": training_split_id,
            "episode_ids": sorted(set(episode_ids)),
            "allowed_source_classes": sorted(set(allowed_source_classes)),
            "allowed_failure_origins": sorted(set(allowed_failure_origins)),
        }
        return cls(
            policy_id=policy_id,
            policy_sha256=_sha256(payload),
            training_split_id=training_split_id,
            episode_ids=tuple(payload["episode_ids"]),
            allowed_source_classes=tuple(payload["allowed_source_classes"]),
            allowed_failure_origins=tuple(payload["allowed_failure_origins"]),
        )


@dataclass(frozen=True)
class EvaluatorEligibilityEvidence:
    source_class: str
    failure_origin: str
    initial_snapshot_pre_feedback: bool
    method_applicable_h_pass: bool
    provenance_complete: bool
    budget_compliant: bool
    hidden_material_redacted: bool
    leakage_audit_pass: bool
    official_hidden_outcome_refs: tuple[str, ...] = ()


def build_training_eligibility_certificate(
    *,
    episode_pack: dict[str, Any],
    initial_project_envelope: dict[str, Any],
    terminal_candidate: dict[str, Any],
    terminal_project_envelope: dict[str, Any],
    qualification_outcome: dict[str, Any],
    policy: TrainingEligibilityPolicy,
    evidence: EvaluatorEligibilityEvidence,
) -> dict[str, Any]:
    """Build a certificate from validated evaluator artifacts, never Recorder labels."""

    _validate_policy(policy)
    _validate_input_artifacts(
        episode_pack=episode_pack,
        initial_project_envelope=initial_project_envelope,
        terminal_candidate=terminal_candidate,
        terminal_project_envelope=terminal_project_envelope,
        qualification_outcome=qualification_outcome,
        policy=policy,
    )
    episode_id = episode_pack["audit_only"]["episode_id"]
    method = episode_pack["audit_only"]["method_condition_id"]
    initial_snapshot_id = _single_snapshot_id(initial_project_envelope)
    terminal_sha256 = _sha256(terminal_candidate)
    qualification_sha256 = _sha256(qualification_outcome)
    official_refs = _official_hidden_refs(qualification_outcome, evidence)
    source_allowed = _source_policy_allowed(policy, evidence)
    checks = {
        "training_split_member": episode_id in policy.episode_ids,
        "requirement_ready": episode_pack["public_context"]["disposition"] == "ready",
        "initial_snapshot_serializable": True,
        "initial_snapshot_pre_feedback": evidence.initial_snapshot_pre_feedback,
        "qualification_completed_pass": (
            qualification_outcome["execution_status"] == "completed"
            and qualification_outcome.get("outcome") == "pass"
        ),
        "trusted_edit_surface_intact": _trusted_surface(
            initial_project_envelope
        )
        == _trusted_surface(terminal_project_envelope),
        "method_applicable_h_pass": evidence.method_applicable_h_pass,
        "provenance_complete": evidence.provenance_complete,
        "budget_compliant": evidence.budget_compliant,
        "hidden_material_redacted": evidence.hidden_material_redacted,
        "leakage_audit_pass": evidence.leakage_audit_pass,
        "source_policy_allowed": source_allowed,
    }
    exclusion_reasons = _exclusion_reasons(checks, len(official_refs))
    evidence_bundle = {
        "episode_pack_sha256": episode_pack["pack_sha256"],
        "initial_project_envelope_sha256": initial_project_envelope["envelope_sha256"],
        "terminal_candidate_sha256": terminal_sha256,
        "terminal_project_envelope_sha256": terminal_project_envelope["envelope_sha256"],
        "qualification_outcome_sha256": qualification_sha256,
        "policy_sha256": policy.policy_sha256,
        "evidence": {
            **asdict(evidence),
            "official_hidden_outcome_refs": _sha256(
                sorted(set(evidence.official_hidden_outcome_refs))
            ),
        },
    }
    payload = {
        "contract_version": TRAINING_ELIGIBILITY_VERSION,
        "visibility_class": "release_internal",
        "episode_id": episode_id,
        "method_condition_id": method,
        "training_split_id": policy.training_split_id,
        "source_class": evidence.source_class,
        "failure_origin": evidence.failure_origin,
        "policy_id": policy.policy_id,
        "policy_sha256": policy.policy_sha256,
        "episode_pack_sha256": episode_pack["pack_sha256"],
        "initial_snapshot_id": initial_snapshot_id,
        "initial_snapshot_sha256": initial_project_envelope["envelope_sha256"],
        "terminal_candidate_sha256": terminal_sha256,
        "project_envelope_sha256": terminal_project_envelope["envelope_sha256"],
        "qualification_outcome_sha256": qualification_sha256,
        "evidence_bundle_sha256": _sha256(evidence_bundle),
        "checks": checks,
        "official_hidden_outcome_ref_count": len(official_refs),
        "eligibility_status": "eligible" if not exclusion_reasons else "ineligible",
        "exclusion_reason_ids": exclusion_reasons,
    }
    artifact = {**payload, "artifact_sha256": _sha256(payload)}
    validate_training_eligibility_certificate(artifact)
    return artifact


def validate_training_eligibility_certificate(artifact: dict[str, Any]) -> None:
    contract = ContractRegistry().load_schema("training_eligibility")
    errors = contract.validate(artifact)
    if errors:
        raise ValueError("invalid training eligibility certificate: " + "; ".join(errors))
    expected = _sha256(
        {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    )
    if artifact["artifact_sha256"] != expected:
        raise ValueError("training eligibility artifact_sha256 mismatch")
    expected_reasons = _exclusion_reasons(
        artifact["checks"], artifact["official_hidden_outcome_ref_count"]
    )
    if artifact["exclusion_reason_ids"] != expected_reasons:
        raise ValueError("training eligibility exclusion reasons are not canonical")
    expected_status = "eligible" if not expected_reasons else "ineligible"
    if artifact["eligibility_status"] != expected_status:
        raise ValueError("training eligibility status disagrees with checks")


def write_training_eligibility_certificate(
    path: Path, artifact: dict[str, Any]
) -> None:
    validate_training_eligibility_certificate(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_policy(policy: TrainingEligibilityPolicy) -> None:
    payload = {
        "policy_id": policy.policy_id,
        "training_split_id": policy.training_split_id,
        "episode_ids": sorted(set(policy.episode_ids)),
        "allowed_source_classes": sorted(set(policy.allowed_source_classes)),
        "allowed_failure_origins": sorted(set(policy.allowed_failure_origins)),
    }
    if not policy.policy_id or not policy.training_split_id:
        raise ValueError("training eligibility policy identifiers must be non-empty")
    if not policy.episode_ids:
        raise ValueError("training eligibility policy requires episode IDs")
    if policy.policy_sha256 != _sha256(payload):
        raise ValueError("training eligibility policy_sha256 mismatch")


def _validate_input_artifacts(
    *,
    episode_pack: dict[str, Any],
    initial_project_envelope: dict[str, Any],
    terminal_candidate: dict[str, Any],
    terminal_project_envelope: dict[str, Any],
    qualification_outcome: dict[str, Any],
    policy: TrainingEligibilityPolicy,
) -> None:
    pack_errors = validate_episode_pack(episode_pack)
    if pack_errors:
        raise ValueError("invalid episode pack: " + "; ".join(pack_errors))
    for label, envelope in (
        ("initial", initial_project_envelope),
        ("terminal", terminal_project_envelope),
    ):
        errors = validate_project_envelope(envelope)
        if errors:
            raise ValueError(f"invalid {label} project envelope: " + "; ".join(errors))
    for key, artifact in (
        ("terminal_candidate", terminal_candidate),
        ("training_qualification_outcome", qualification_outcome),
    ):
        errors = ContractRegistry().load_schema(key).validate(artifact)
        if errors:
            raise ValueError(f"invalid {key}: " + "; ".join(errors))

    episode_id = episode_pack["audit_only"]["episode_id"]
    method = episode_pack["audit_only"]["method_condition_id"]
    terminal_sha256 = _sha256(terminal_candidate)
    bindings = (
        (initial_project_envelope["episode_id"], episode_id, "initial envelope episode"),
        (terminal_project_envelope["episode_id"], episode_id, "terminal envelope episode"),
        (terminal_candidate["episode_id"], episode_id, "terminal candidate episode"),
        (qualification_outcome["episode_id"], episode_id, "qualification episode"),
        (initial_project_envelope["method_condition_id"], method, "initial envelope method"),
        (terminal_project_envelope["method_condition_id"], method, "terminal envelope method"),
        (terminal_candidate["method_condition_id"], method, "terminal candidate method"),
        (qualification_outcome["method_condition_id"], method, "qualification method"),
        (
            terminal_candidate["requirement_projection_sha256"],
            episode_pack["public_context"]["public_projection_sha256"],
            "requirement projection",
        ),
        (
            terminal_candidate["project_envelope_sha256"],
            terminal_project_envelope["envelope_sha256"],
            "terminal project envelope",
        ),
        (
            qualification_outcome["terminal_candidate_sha256"],
            terminal_sha256,
            "qualification terminal candidate",
        ),
        (
            qualification_outcome["public_pack_sha256"],
            episode_pack["pack_sha256"],
            "qualification public pack",
        ),
        (
            qualification_outcome["training_split_id"],
            policy.training_split_id,
            "qualification training split",
        ),
        (
            initial_project_envelope["method_policy_sha256"],
            terminal_project_envelope["method_policy_sha256"],
            "method policy",
        ),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise ValueError(f"training eligibility artifact binding mismatch: {label}")
    terminal_files = {
        item["path"]: item["sha256"] for item in terminal_candidate["project_files"]
    }
    envelope_files = {
        item["path"]: item["sha256"] for item in terminal_project_envelope["files"]
    }
    if terminal_files != envelope_files:
        raise ValueError("training eligibility terminal file binding mismatch")
    _single_snapshot_id(initial_project_envelope)


def _single_snapshot_id(envelope: dict[str, Any]) -> str:
    snapshot_ids = {item["snapshot_id"] for item in envelope["files"]}
    if len(snapshot_ids) != 1:
        raise ValueError("initial project envelope must bind exactly one snapshot_id")
    return next(iter(snapshot_ids))


def _trusted_surface(envelope: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    records: list[tuple[str, str, str]] = []
    for file in envelope["files"]:
        if file["owner"] == "trusted_builder":
            records.append((file["path"], "file", file["sha256"]))
        for region in file.get("regions", ()):
            if region["owner"] == "trusted_builder":
                records.append((file["path"], region["region_id"], region["sha256"]))
    return tuple(sorted(records))


def _source_policy_allowed(
    policy: TrainingEligibilityPolicy,
    evidence: EvaluatorEligibilityEvidence,
) -> bool:
    source = evidence.source_class.lower()
    origin = evidence.failure_origin.lower()
    return (
        source not in _HARD_EXCLUDED_SOURCE_CLASSES
        and origin not in _HARD_EXCLUDED_FAILURE_ORIGINS
        and evidence.source_class in policy.allowed_source_classes
        and evidence.failure_origin in policy.allowed_failure_origins
    )


def _official_hidden_refs(
    qualification: dict[str, Any],
    evidence: EvaluatorEligibilityEvidence,
) -> tuple[str, ...]:
    refs = set(evidence.official_hidden_outcome_refs)
    for ref in qualification["evaluator_evidence_refs"]:
        normalized = ref.lower().replace("-", "_")
        if "official_hidden_outcome" in normalized:
            refs.add(ref)
    return tuple(sorted(refs))


def _exclusion_reasons(
    checks: dict[str, bool], official_hidden_outcome_ref_count: int
) -> list[str]:
    reasons = [reason for key, reason in _CHECK_REASON_IDS.items() if not checks[key]]
    if official_hidden_outcome_ref_count:
        reasons.append("official_hidden_outcome_reference_present")
    return sorted(reasons)


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
