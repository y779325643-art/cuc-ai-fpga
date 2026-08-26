import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "contracts" / "trajectory" / "trajectory-v1.schema.json"
SCHEMA_V2_PATH = REPO_ROOT / "contracts" / "trajectory" / "trajectory-v2.schema.json"
EXPECTED_STAGE_STATUSES = [
    "pass",
    "fail",
    "not_run",
    "infrastructure_error",
]
EXPECTED_VERIFICATION_STAGES = {
    "l0",
    "l1",
    "l2",
    "l3",
    "l4_open",
    "l4_commercial",
    "l5",
}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def find_definition_enum(node: object, key: str) -> list[str]:
    if isinstance(node, dict):
        if key in node and isinstance(node[key], dict) and "enum" in node[key]:
            return node[key]["enum"]
        for value in node.values():
            found = find_definition_enum(value, key)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_definition_enum(value, key)
            if found:
                return found
    return []


def test_trajectory_schema_identity_and_required_fields() -> None:
    schema = load_schema()
    assert schema["$id"] == "https://sr2fpga.local/contracts/trajectory/v1"
    assert {
        "episode_id",
        "requirement",
        "his_validation",
        "verification",
        "attempts",
    } <= set(schema["required"])


def test_trajectory_schema_has_distinct_stage_statuses() -> None:
    schema = load_schema()
    assert schema["$defs"]["stage_status"]["enum"] == EXPECTED_STAGE_STATUSES
    assert find_definition_enum(schema, "stage_status") == EXPECTED_STAGE_STATUSES


def test_trajectory_schema_covers_l0_through_l5() -> None:
    verification = load_schema()["$defs"]["verification"]
    assert EXPECTED_VERIFICATION_STAGES <= set(verification["properties"])
    for stage in ("l4_open", "l4_commercial"):
        assert verification["properties"][stage]["$ref"] == "#/$defs/stage_record"


def test_stage_skip_reason_is_conditional() -> None:
    stage_record = load_schema()["$defs"]["stage_record"]
    rules = stage_record["allOf"]
    not_run_rule = next(
        rule
        for rule in rules
        if set(rule["if"]["properties"]["status"]["enum"])
        == {"not_run", "infrastructure_error"}
    )
    assert "skip_reason" in not_run_rule["then"]["required"]
    completed_rule = next(
        rule
        for rule in rules
        if set(rule["if"]["properties"]["status"]["enum"]) == {"pass", "fail"}
    )
    assert completed_rule["then"]["not"]["required"] == ["skip_reason"]


def _trajectory_v2() -> dict:
    artifact_ref = {
        "key": "cost-summaries/episode-001/attempt-000",
        "sha256": "a" * 64,
        "size_bytes": 1,
        "media_type": "application/json",
    }
    return {
        "contract_version": "trajectory-v2",
        "trajectory_id": "trajectory-v2-" + "b" * 64,
        "episode_id": "episode-001",
        "method_condition": "M0",
        "failure_origin": "natural_llm",
        "attempts": [
            {
                "attempt_id": "attempt-000",
                "candidate_id": "episode-001-attempt-000",
                "input_artifact_hashes": ["c" * 64],
                "output_artifact_hashes": ["d" * 64],
                "attempt_event_refs": [
                    artifact_ref
                    | {"key": "attempt-events/episode-001/attempt-000/000000"}
                ],
                "cost_summary_ref": artifact_ref,
                "source_events_sha256": "e" * 64,
                "accounting_closed": True,
            }
        ],
        "terminal_candidate_ref": None,
        "development_hidden_outcome_ref": None,
        "lineage_complete": False,
        "missing_lineage_reasons": ["terminal_candidate_ref_missing"],
    }


def test_trajectory_v2_requires_event_derived_cost_and_explicit_missing_lineage() -> None:
    schema = json.loads(SCHEMA_V2_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(_trajectory_v2())

    false_complete = copy.deepcopy(_trajectory_v2())
    false_complete["lineage_complete"] = True
    false_complete["missing_lineage_reasons"] = []
    with pytest.raises(ValidationError):
        validator.validate(false_complete)


def test_trajectory_v2_hidden_reference_is_opaque_and_closed() -> None:
    schema = json.loads(SCHEMA_V2_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    payload = _trajectory_v2()
    payload["development_hidden_outcome_ref"] = {
        "outcome_id": "hidden-outcome-" + "f" * 64,
        "contract_id": "development-hidden-outcome-v1",
    }
    validator.validate(payload)

    payload["development_hidden_outcome_ref"]["status"] = "pass"
    with pytest.raises(ValidationError):
        validator.validate(payload)
