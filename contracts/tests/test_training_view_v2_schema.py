import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/training-views/training-view-row-v2.schema.json").read_text(
        encoding="utf-8"
    )
)


def _row(treatment="M6F"):
    target = {
        "kind": "project_files",
        "files": [{"path": "rtl/top.sv", "role": "rtl", "content": "module top; endmodule"}],
    }
    if treatment == "M6T":
        target = {
            "kind": "public_transition",
            "public_failure": {"stage": "L2", "reason": "mismatch"},
            "public_diagnosis": {"reason": "counter priority"},
            "public_patch": "fix priority",
            "public_rerun": {"outcome": "pass"},
            "final_files": [
                {"path": "rtl/top.sv", "role": "rtl", "content": "module top; endmodule"}
            ],
        }
    return {
        "contract_version": "training-view-row-v2",
        "row_id": "row-001",
        "row_sha256": "a" * 64,
        "source_episode_id": "episode-001",
        "snapshot_id": "snapshot-final",
        "treatment": treatment,
        "payload": {
            "prompt_messages": [
                {"role": "user", "content": "Generate the counter project."}
            ],
            "assistant_target": target,
        },
    }


def test_training_view_v2_schema_is_closed_and_accepts_project_treatment() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    Draft202012Validator(SCHEMA).validate(_row())
    assert SCHEMA["additionalProperties"] is False


def test_training_view_v2_requires_transition_target_for_m6t() -> None:
    Draft202012Validator(SCHEMA).validate(_row("M6T"))
    invalid = _row("M6T")
    invalid["payload"]["assistant_target"] = _row("M6F")["payload"]["assistant_target"]
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(invalid)


def test_training_view_v2_rejects_transition_target_for_m6u() -> None:
    invalid = _row("M6U")
    invalid["payload"]["assistant_target"] = _row("M6T")["payload"]["assistant_target"]
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(invalid)


def test_training_view_v2_rejects_unknown_envelope_field() -> None:
    invalid = copy.deepcopy(_row())
    invalid["eligibility_reason"] = "qualified"
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(invalid)
