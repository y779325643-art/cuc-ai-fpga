import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/requirement-audit/ambiguity-outcome-v1.schema.json").read_text(
        encoding="utf-8"
    )
)


def _rate():
    return {"numerator": 0, "denominator": 1, "value": 0.0}


def _precision_recall():
    return {
        "true_positive_count": 0,
        "predicted_count": 0,
        "gold_count": 0,
        "precision": None,
        "recall": None,
    }


def _audit_cost():
    return {
        "counters": {
            "model_calls": 0,
            "tool_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "wall_time_ms": 0.0,
        },
        "infrastructure_status_counts": {
            "available": 1,
            "unavailable": 0,
            "error": 0,
        },
    }


def _artifact():
    counts = {"ready": 0, "needs_clarification": 0, "capability_gap": 0}
    return {
        "contract_version": "ambiguity-outcome-v1",
        "artifact_sha256": "a" * 64,
        "audit_run_id": "audit-001",
        "manifest_sha256": "b" * 64,
        "witness_artifact_sha256": "d" * 64,
        "visibility_class": "evaluator_only",
        "observations": [
            {
                "observation_id": "seed-000",
                "phase_a_audit_sha256": "c" * 64,
                "event_artifact_sha256": "e" * 64,
                "replay_artifact_sha256": None,
                "case_count": 1,
                "completed_count": 1,
                "not_run_count": 0,
                "audit_cost": _audit_cost(),
            }
        ],
        "clusters": [
            {
                "base_requirement_cluster_id": "cluster-001",
                "case_ids": ["case-001"],
                "case_observation_count": 1,
                "not_run_count": 0,
                "false_proceed_count": 0,
                "generation_boundary_violation_count": 0,
                "replay_eligible_count": 0,
                "replay_closed_count": 0,
                "counterfactual_eligible_observation_count": 0,
                "counterfactual_consistent_observation_count": 0,
                "primary_safety_failure": False,
            }
        ],
        "summary": {
            "cluster_count": 1,
            "observation_count": 1,
            "case_observation_count": 1,
            "semantic_case_observation_count": 1,
            "not_run_count": 0,
            "confusion_matrix": {key: dict(counts) for key in counts},
            "fp_amb": _rate(),
            "fp_gap": _rate(),
            "primary_safety_max_false_proceed_rate": 0.0,
            "ready_fully_specified_false_block": _rate(),
            "ready_permitted_default_false_block": _rate(),
            "one_replay_closure": _rate(),
            "critical_fact_precision_recall": _precision_recall(),
            "capability_precision_recall": _precision_recall(),
            "permitted_default_precision_recall": _precision_recall(),
            "explicit_assumption_precision_recall": _precision_recall(),
            "repeated_known_fact_question": _rate(),
            "unknown_family_coercion": _rate(),
            "counterfactual_consistency": {
                "numerator": 0,
                "denominator": 0,
                "value": None,
            },
            "cluster_primary_safety_failure": _rate(),
            "generation_boundary_violation_count": 0,
            "audit_cost": _audit_cost(),
            "interval_status": "not_frozen",
            "interval_not_frozen_reason": "G4b has not frozen intervals",
        },
    }


def test_ambiguity_outcome_schema_is_closed_and_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    Draft202012Validator(SCHEMA).validate(_artifact())
    assert SCHEMA["additionalProperties"] is False


def test_outcome_rejects_invented_frozen_interval() -> None:
    artifact = copy.deepcopy(_artifact())
    artifact["summary"]["interval_status"] = "frozen"
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(artifact)


def test_outcome_allows_null_rate_only_when_runtime_has_no_denominator_shape() -> None:
    artifact = copy.deepcopy(_artifact())
    artifact["summary"]["fp_gap"] = {
        "numerator": 0,
        "denominator": 0,
        "value": None,
    }
    Draft202012Validator(SCHEMA).validate(artifact)
