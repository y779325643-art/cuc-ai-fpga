import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/training-release/training-eligibility-v1.schema.json").read_text(
        encoding="utf-8"
    )
)


def _certificate() -> dict[str, object]:
    checks = {
        "training_split_member": True,
        "requirement_ready": True,
        "initial_snapshot_serializable": True,
        "initial_snapshot_pre_feedback": True,
        "qualification_completed_pass": True,
        "trusted_edit_surface_intact": True,
        "method_applicable_h_pass": True,
        "provenance_complete": True,
        "budget_compliant": True,
        "hidden_material_redacted": True,
        "leakage_audit_pass": True,
        "source_policy_allowed": True,
    }
    return {
        "contract_version": "training-eligibility-v1",
        "artifact_sha256": "a" * 64,
        "visibility_class": "release_internal",
        "episode_id": "episode-001",
        "method_condition_id": "M0",
        "training_split_id": "train-split-dev",
        "source_class": "model_generated",
        "failure_origin": "natural_llm",
        "policy_id": "development-training-policy",
        "policy_sha256": "b" * 64,
        "episode_pack_sha256": "c" * 64,
        "initial_snapshot_id": "snapshot-initial",
        "initial_snapshot_sha256": "d" * 64,
        "terminal_candidate_sha256": "e" * 64,
        "project_envelope_sha256": "f" * 64,
        "qualification_outcome_sha256": "0" * 64,
        "evidence_bundle_sha256": "1" * 64,
        "checks": checks,
        "official_hidden_outcome_ref_count": 0,
        "eligibility_status": "eligible",
        "exclusion_reason_ids": [],
    }


def _errors(payload: dict[str, object]) -> tuple[str, ...]:
    return tuple(error.message for error in Draft202012Validator(SCHEMA).iter_errors(payload))


def test_training_eligibility_schema_accepts_eligible_certificate() -> None:
    assert _errors(_certificate()) == ()


def test_training_eligibility_schema_rejects_unknown_fields() -> None:
    payload = _certificate()
    payload["recorder_label"] = "success"

    assert any("recorder_label" in error for error in _errors(payload))


def test_eligible_certificate_requires_every_check_true() -> None:
    payload = _certificate()
    payload["checks"]["qualification_completed_pass"] = False  # type: ignore[index]

    assert _errors(payload)


def test_ineligible_certificate_requires_an_exclusion_reason() -> None:
    payload = copy.deepcopy(_certificate())
    payload["eligibility_status"] = "ineligible"

    assert _errors(payload)
