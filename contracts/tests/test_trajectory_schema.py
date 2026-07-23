import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "contracts" / "trajectory" / "trajectory-v1.schema.json"
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
    assert "not_run" != "fail"


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
