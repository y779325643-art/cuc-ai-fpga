import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/requirement-audit/clarification-replay-v1.schema.json").read_text(
        encoding="utf-8"
    )
)


def _artifact() -> dict:
    return {
        "contract_version": "clarification-replay-v1",
        "artifact_sha256": "a" * 64,
        "audit_run_id": "audit-001",
        "manifest_sha256": "b" * 64,
        "phase_a_audit_sha256": "c" * 64,
        "visibility_class": "evaluator_only",
        "replays": [
            {
                "base_requirement_cluster_id": "cluster-001",
                "ambiguity_case_id": "case-001",
                "branch_id": "answer-001",
                "phase_a_case_sha256": "d" * 64,
                "answer_sha256": "e" * 64,
                "lineage_sha256": "f" * 64,
                "one_shot_marker_sha256": "0" * 64,
                "replayed_fact_ids": ["interface_protocols"],
                "expected_replay_disposition": "ready",
                "actual_replay_disposition": "ready",
                "closure": True,
                "generation_boundary_crossed": False,
                "counters": {
                    "model_calls": 0,
                    "tool_calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "wall_time_ms": 1.0,
                },
            }
        ],
    }


def test_clarification_replay_schema_is_closed_and_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    Draft202012Validator(SCHEMA).validate(_artifact())
    assert SCHEMA["additionalProperties"] is False


def test_replay_may_record_failure_to_close_as_needs_clarification() -> None:
    artifact = _artifact()
    artifact["replays"][0]["actual_replay_disposition"] = "needs_clarification"
    artifact["replays"][0]["closure"] = False
    Draft202012Validator(SCHEMA).validate(artifact)


@pytest.mark.parametrize(
    ("field", "value"),
    [("generation_boundary_crossed", True), ("actual_replay_disposition", "not_run")],
)
def test_replay_rejects_boundary_escape_and_invalid_semantic_status(field, value) -> None:
    artifact = copy.deepcopy(_artifact())
    artifact["replays"][0][field] = value
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(artifact)
