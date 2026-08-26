import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/requirement-audit/ambiguity-audit-events-v1.schema.json").read_text(
        encoding="utf-8"
    )
)


def _artifact():
    return {
        "contract_version": "ambiguity-audit-events-v1",
        "artifact_sha256": "a" * 64,
        "audit_run_id": "audit-001",
        "manifest_sha256": "b" * 64,
        "phase_a_audit_sha256": "c" * 64,
        "visibility_class": "evaluator_only",
        "events": [
            {
                "sequence": 0,
                "ambiguity_case_id": "case-001",
                "event_type": "phase_a_started",
            },
            {
                "sequence": 1,
                "ambiguity_case_id": "case-001",
                "event_type": "phase_a_completed",
                "execution_status": "completed",
                "predicted_disposition": "needs_clarification",
                "infrastructure_status": "available",
                "counters": {
                    "model_calls": 0,
                    "tool_calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "wall_time_ms": 1.0,
                },
            },
            {
                "sequence": 2,
                "ambiguity_case_id": "case-001",
                "event_type": "downstream_attempt",
                "downstream_kind": "project_generator_call",
                "enforcement_status": "intercepted",
            },
        ],
    }


def test_ambiguity_audit_events_schema_is_closed_and_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    Draft202012Validator(SCHEMA).validate(_artifact())
    assert SCHEMA["additionalProperties"] is False


def test_downstream_attempt_requires_kind_and_enforcement_status() -> None:
    artifact = copy.deepcopy(_artifact())
    artifact["events"][2].pop("enforcement_status")
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(artifact)


def test_phase_event_rejects_downstream_fields() -> None:
    artifact = copy.deepcopy(_artifact())
    artifact["events"][0]["downstream_kind"] = "req2his_call"
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(artifact)


def test_not_run_completion_requires_reason_and_nonavailable_infrastructure() -> None:
    artifact = copy.deepcopy(_artifact())
    completion = artifact["events"][1]
    completion["execution_status"] = "not_run"
    completion["infrastructure_status"] = "unavailable"
    completion["not_run_reason_id"] = "provider_unavailable"
    completion.pop("predicted_disposition")
    Draft202012Validator(SCHEMA).validate(artifact)

    completion.pop("not_run_reason_id")
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(artifact)
