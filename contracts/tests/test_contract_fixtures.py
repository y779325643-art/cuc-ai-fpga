import json
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "contracts" / "tests" / "fixtures"
FIXTURES = {
    "system_his": (
        FIXTURE_ROOT / "system_his_minimal_v1_2.json",
        REPO_ROOT / "contracts" / "system-his" / "system-his-v1.2.schema.json",
    ),
    "trajectory": (
        FIXTURE_ROOT / "trajectory_minimal_v1.json",
        REPO_ROOT / "contracts" / "trajectory" / "trajectory-v1.schema.json",
    ),
    "training_view": (
        FIXTURE_ROOT / "training_view_req2file_v1.json",
        REPO_ROOT
        / "contracts"
        / "training-views"
        / "training-view-row-v1.schema.json",
    ),
}
FILE_PATH_KEYS = {
    "source",
    "testbench",
    "constraints",
    "rtl_sources",
    "manifest",
    "predicted_qor",
    "path",
    "report_paths",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def path_values(node: object, parent_key: str = "") -> list[str]:
    values: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if (
                key in FILE_PATH_KEYS
                or key.endswith("_path")
                or key.endswith("_paths")
            ):
                if isinstance(value, str):
                    values.append(value)
                elif isinstance(value, list):
                    values.extend(item for item in value if isinstance(item, str))
            values.extend(path_values(value, key))
    elif isinstance(node, list):
        for value in node:
            values.extend(path_values(value, parent_key))
    return values


def test_contract_fixtures_parse_and_cover_schema_requirements() -> None:
    for name, (fixture_path, schema_path) in FIXTURES.items():
        fixture = load_json(fixture_path)
        schema = load_json(schema_path)
        assert set(schema["required"]) <= set(fixture), name
        for property_name, property_schema in schema["properties"].items():
            if property_name in fixture and "const" in property_schema:
                assert fixture[property_name] == property_schema["const"], (
                    name,
                    property_name,
                )


def test_all_fixture_paths_are_repository_relative() -> None:
    for name, (fixture_path, _) in FIXTURES.items():
        for value in path_values(load_json(fixture_path)):
            path = PurePosixPath(value)
            assert value, name
            assert not path.is_absolute(), (name, value)
            assert not Path(value).is_absolute(), (name, value)
            assert ".." not in path.parts, (name, value)


def test_req2file_fixture_has_no_standalone_pass_credit() -> None:
    fixture = load_json(FIXTURES["training_view"][0])
    assert fixture["view_type"] == "requirement_to_file"
    assert fixture["source_episode_id"] == "fixture-episode-001"
    assert fixture["official_eval_unit"] is False
    assert fixture["standalone_pass_credit"] is False


def test_trajectory_not_run_stages_explain_why() -> None:
    trajectory = load_json(FIXTURES["trajectory"][0])
    stages = trajectory["verification"].values()
    not_run_stages = [stage for stage in stages if stage["status"] == "not_run"]
    assert not_run_stages
    assert all(stage.get("skip_reason") for stage in not_run_stages)


def test_infrastructure_error_is_distinct_from_model_failure() -> None:
    trajectory = load_json(FIXTURES["trajectory"][0])
    statuses = {stage["status"] for stage in trajectory["verification"].values()}
    assert "fail" in statuses
    assert "infrastructure_error" in statuses
    assert "fail" != "infrastructure_error"
