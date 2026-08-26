import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "contracts"
    / "evaluation"
    / "development-l4-qor-provenance-v1.schema.json"
)


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _incomplete_payload() -> dict:
    return {
        "contract_version": "development-l4-qor-provenance-v1",
        "lane": "l4_open",
        "source_stage": "pnr",
        "source_stage_status": "pass",
        "core_tool_environment_ref": {
            "key": "tool-environments/development-preflight",
            "sha256": "a" * 64,
            "size_bytes": 100,
            "media_type": "application/json",
        },
        "l4_tool_environment_ref": {
            "key": "tool-environments/development-l4-preflight",
            "sha256": "c" * 64,
            "size_bytes": 100,
            "media_type": "application/json",
        },
        "raw_evidence_refs": [
            {
                "path": "attempts/attempt_000/eval/pnr.json",
                "sha256": "b" * 64,
                "size_bytes": 200,
            }
        ],
        "l4_tool_version_status": "not_captured",
        "l4_tool_version": None,
        "provenance_status": "incomplete",
        "incomplete_reasons": ["l4_tool_version_not_captured"],
        "terminal_binding": False,
        "pass_credit_authority": False,
        "official_authority": False,
    }


def test_incomplete_l4_provenance_preserves_raw_hashes_without_overclaim() -> None:
    _validator().validate(_incomplete_payload())


def test_complete_l4_provenance_requires_version_raw_evidence_and_no_gap() -> None:
    payload = _incomplete_payload()
    payload["provenance_status"] = "complete"

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("terminal_binding", True),
        ("pass_credit_authority", True),
        ("official_authority", True),
    ),
)
def test_development_l4_provenance_rejects_authority_escalation(field, value) -> None:
    payload = copy.deepcopy(_incomplete_payload())
    payload[field] = value

    with pytest.raises(ValidationError):
        _validator().validate(payload)
