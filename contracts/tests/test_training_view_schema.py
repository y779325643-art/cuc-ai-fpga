import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT
    / "contracts"
    / "training-views"
    / "training-view-row-v1.schema.json"
)
EXPECTED_VIEW_TYPES = {
    "requirement_to_his",
    "his_to_project",
    "requirement_to_project",
    "requirement_to_file",
    "failure_to_diagnosis",
    "failure_to_patch",
    "project_to_predicted_qor",
    "project_to_measured_qor",
}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_training_view_schema_declares_all_views() -> None:
    schema = load_schema()
    assert set(schema["properties"]["view_type"]["enum"]) == EXPECTED_VIEW_TYPES


def test_requirement_to_file_is_a_derived_non_evaluation_view() -> None:
    schema = load_schema()
    rule = next(
        item
        for item in schema["allOf"]
        if item["if"]["properties"]["view_type"].get("const")
        == "requirement_to_file"
    )
    assert {
        "source_episode_id",
        "file_role",
        "path",
        "official_eval_unit",
        "standalone_pass_credit",
    } <= set(rule["then"]["required"])
    properties = rule["then"]["properties"]
    assert properties["source_episode_id"]["minLength"] == 1
    assert properties["official_eval_unit"]["const"] is False
    assert properties["standalone_pass_credit"]["const"] is False
    assert properties["path"]["$ref"] == "#/$defs/relative_path"
