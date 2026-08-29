import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "contracts"
    / "accounting"
    / "development-block-preparation-event-v1.schema.json"
)
HASH = "a" * 64
AXES = (
    "logical_model_calls",
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "provider_transport_attempts",
    "planner_parser_schema_retries",
    "outer_repair_attempts",
    "public_tool_calls",
    "hidden_evaluator_tool_calls",
    "hidden_infrastructure_retries",
    "wall_time",
    "eda_time",
    "hidden_evaluator_runtime",
)


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _ref(key: str) -> dict:
    return {
        "key": key,
        "sha256": HASH,
        "size_bytes": 1,
        "media_type": "application/json",
    }


def _event() -> dict:
    return {
        "contract_version": "development-block-preparation-event-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "event_id": "block-preparation-event-" + HASH,
        "parent_event_id": "block-preparation-event-" + "b" * 64,
        "sequence": 2,
        "paired_block_ref": _ref("paired/" + HASH + "/paired-block"),
        "checkpoint_id": "direct_initial_project",
        "parent_checkpoint_ids": [],
        "stage": "block_direct_initial",
        "event_kind": "checkpoint_materialized",
        "status": "completed",
        "reason": None,
        "started_at": 1.0,
        "duration_seconds": None,
        "input_artifact_refs": [],
        "output_artifact_refs": [_ref("paired/" + HASH + "/project")],
        "input_artifact_hashes": [],
        "output_artifact_hashes": [HASH],
        "budget_reservation": None,
        "cost_delta": {axis: 0 for axis in AXES},
        "unavailable_axes": {},
        "model_gateway_provenance_ref": None,
        "failure_origin": "natural_llm",
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }


def _close_event() -> dict:
    payload = _event()
    payload.update(
        {
            "parent_event_id": "block-preparation-event-" + HASH,
            "sequence": 3,
            "checkpoint_id": None,
            "stage": "accounting_close",
            "event_kind": "accounting_closed",
            "status": "closed",
            "output_artifact_refs": [],
            "output_artifact_hashes": [],
        }
    )
    return payload


def test_block_preparation_event_is_method_neutral() -> None:
    payload = _event()
    assert "method_condition" not in payload
    _validator().validate(payload)
    _validator().validate(_close_event())


def test_block_preparation_event_rejects_method_owner() -> None:
    payload = _event()
    payload["method_condition"] = "M4"

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_block_preparation_event_rejects_unknown_checkpoint_and_invalid_parent() -> None:
    unknown_checkpoint = _event()
    unknown_checkpoint["checkpoint_id"] = "unknown_checkpoint"
    invalid_parent = _event()
    invalid_parent["parent_checkpoint_ids"] = ["shared_system_his"]

    with pytest.raises(ValidationError):
        _validator().validate(unknown_checkpoint)
    with pytest.raises(ValidationError):
        _validator().validate(invalid_parent)


def test_block_preparation_event_rejects_missing_axis_and_unavailable_without_reason() -> None:
    missing_axis = _close_event()
    missing_axis["cost_delta"].pop("eda_time")
    unavailable_without_reason = _event()
    unavailable_without_reason["cost_delta"]["input_tokens"] = None

    with pytest.raises(ValidationError):
        _validator().validate(missing_axis)
    with pytest.raises(ValidationError):
        _validator().validate(unavailable_without_reason)


def test_non_close_events_require_a_checkpoint_and_matching_stage() -> None:
    no_checkpoint = _event()
    no_checkpoint.update(
        {
            "checkpoint_id": None,
            "stage": "accounting_close",
            "event_kind": "axis_cost",
            "status": "completed",
        }
    )
    mismatched_stage = _event()
    mismatched_stage.update(
        {"event_kind": "axis_cost", "status": "completed", "stage": "accounting_close"}
    )

    with pytest.raises(ValidationError):
        _validator().validate(no_checkpoint)
    with pytest.raises(ValidationError):
        _validator().validate(mismatched_stage)


def test_unavailable_axes_require_exact_null_delta_correspondence() -> None:
    valid_unavailable = _event()
    valid_unavailable.update({"event_kind": "axis_cost", "status": "completed"})
    valid_unavailable["cost_delta"]["input_tokens"] = None
    valid_unavailable["unavailable_axes"] = {"input_tokens": "provider_missing"}
    numeric_with_reason = copy.deepcopy(valid_unavailable)
    numeric_with_reason["cost_delta"]["input_tokens"] = 0
    absent_with_reason = copy.deepcopy(valid_unavailable)
    absent_with_reason["cost_delta"].pop("input_tokens")

    _validator().validate(valid_unavailable)
    with pytest.raises(ValidationError):
        _validator().validate(numeric_with_reason)
    with pytest.raises(ValidationError):
        _validator().validate(absent_with_reason)


@pytest.mark.parametrize(
    "field",
    (
        "official_outcome",
        "official_authority",
        "pass_credit_authority",
        "rq1_evidence",
        "rq2_evidence",
        "g3_accepted",
        "g4b_authorized",
    ),
)
def test_block_preparation_event_rejects_authority_escalation(field: str) -> None:
    payload = _event()
    payload[field] = True

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_block_preparation_event_rejects_wrong_version_and_unknown_field() -> None:
    wrong_version = _event()
    wrong_version["contract_version"] = "development-block-preparation-event-v2"
    unknown = copy.deepcopy(_event())
    unknown["private_trace"] = True

    with pytest.raises(ValidationError):
        _validator().validate(wrong_version)
    with pytest.raises(ValidationError):
        _validator().validate(unknown)
