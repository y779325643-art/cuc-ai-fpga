import json
from pathlib import Path
from typing import Iterator

import pytest
from jsonschema import Draft202012Validator, ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT / "contracts" / "system-his" / "system-his-v1.2.schema.json"
)
FIXTURE_PATH = (
    REPO_ROOT / "contracts" / "tests" / "fixtures" / "system_his_minimal_v1_2.json"
)
REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "intent",
    "top",
    "state",
    "components",
    "instances",
    "data_flow",
    "control_flow",
    "timing",
    "resources",
    "verification",
    "artifacts",
}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def validate(instance: dict) -> None:
    Draft202012Validator(load_schema()).validate(instance)


def nested_errors(error: ValidationError) -> Iterator[ValidationError]:
    yield error
    for child in error.context:
        yield from nested_errors(child)


def test_system_his_schema_identity_and_closed_top_level() -> None:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "https://sr2fpga.local/contracts/system-his/v1.2"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False


def test_system_his_schema_requires_canonical_v12_fields() -> None:
    schema = load_schema()
    assert set(schema["required"]) == REQUIRED_TOP_LEVEL_KEYS
    assert schema["properties"]["schema_version"]["const"] == "system-his-v1.2"


def test_system_his_fixture_validates_as_draft_2020_12_instance() -> None:
    validate(load_fixture())


def test_system_his_accepts_canonical_parameterized_width() -> None:
    instance = load_fixture()
    instance["top"]["ports"][-1]["width"] = {
        "expr": "DATA_WIDTH",
        "resolved": 8,
    }
    validate(instance)


def test_system_his_accepts_compatibility_direction_and_reset_spellings() -> None:
    instance = load_fixture()
    port = instance["top"]["ports"][0]
    port["direction"] = port.pop("dir")
    reset = instance["top"]["resets"][0]
    reset["polarity"] = "high"
    reset["kind"] = "synchronous"
    validate(instance)


def test_system_his_accepts_typed_connection_and_combinational_declaration() -> None:
    instance = load_fixture()
    instance["components"][0]["combinational"] = False
    instance["data_flow"][0]["connections"] = [
        {"from": "top.enable", "to": "counter.enable", "width": 1}
    ]

    validate(instance)


def test_system_his_rejects_invalid_typed_connection_shape() -> None:
    instance = load_fixture()
    instance["data_flow"][0]["connections"] = [
        {"from": "top.enable", "to": "counter.enable", "width": 1, "note": "untyped"}
    ]

    errors = list(Draft202012Validator(load_schema()).iter_errors(instance))

    assert errors
    assert any(error.validator == "additionalProperties" for error in errors)


def test_system_his_rejects_non_boolean_combinational_declaration() -> None:
    instance = load_fixture()
    instance["components"][0]["combinational"] = "yes"

    errors = list(Draft202012Validator(load_schema()).iter_errors(instance))

    assert errors
    assert any("combinational" in list(error.absolute_path) for error in errors)


@pytest.mark.parametrize(
    ("width", "expected_validator"),
    [
        ({"expr": "DATA_WIDTH"}, "required"),
        ({"expr": "DATA_WIDTH", "resolved": 0}, "minimum"),
        ({"expr": "", "resolved": 8}, "minLength"),
        ({"expr": "DATA_WIDTH", "resolved": 8, "bits": 8}, "additionalProperties"),
    ],
)
def test_system_his_rejects_invalid_parameterized_width(
    width: object,
    expected_validator: str,
) -> None:
    instance = load_fixture()
    instance["top"]["ports"][-1]["width"] = width

    errors = list(Draft202012Validator(load_schema()).iter_errors(instance))

    assert errors
    assert any(
        nested.validator == expected_validator
        for error in errors
        for nested in nested_errors(error)
    )


def test_system_his_rejects_port_without_direction() -> None:
    instance = load_fixture()
    instance["top"]["ports"][0].pop("dir")

    errors = list(Draft202012Validator(load_schema()).iter_errors(instance))

    assert errors
    assert any(error.validator == "anyOf" for error in errors)


def test_system_his_rejects_unknown_port_direction() -> None:
    instance = load_fixture()
    instance["top"]["ports"][0]["dir"] = "source"

    errors = list(Draft202012Validator(load_schema()).iter_errors(instance))

    assert errors
    assert any("dir" in list(error.absolute_path) for error in errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("polarity", "negative"),
        ("kind", "clocked"),
    ],
)
def test_system_his_rejects_unknown_reset_spelling(field: str, value: str) -> None:
    instance = load_fixture()
    instance["top"]["resets"][0][field] = value

    errors = list(Draft202012Validator(load_schema()).iter_errors(instance))

    assert errors
    assert any(field in list(error.absolute_path) for error in errors)


def test_system_his_rejects_missing_required_top_level_section() -> None:
    instance = load_fixture()
    instance.pop("artifacts")

    errors = list(Draft202012Validator(load_schema()).iter_errors(instance))

    assert errors
    assert any(error.validator == "required" for error in errors)
