import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
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


def _validator(relative: str) -> Draft202012Validator:
    schema = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _close_event() -> dict:
    return {
        "contract_version": "attempt-event-v1",
        "event_id": "attempt-event-" + HASH,
        "parent_event_id": None,
        "sequence": 0,
        "episode_id": "episode-001",
        "candidate_id": None,
        "attempt_id": "attempt-001",
        "method_condition": "M0",
        "stage": "accounting_close",
        "visibility_class": "accounting",
        "event_type": "accounting_closed",
        "status": "closed",
        "started_at": 1.0,
        "duration_seconds": None,
        "input_artifact_hashes": [],
        "output_artifact_hashes": [],
        "budget_reservation": None,
        "cost_delta": {axis: 0 for axis in AXES},
        "unavailable_axes": {},
        "failure_origin": "synthetic_injected",
    }


def _summary() -> dict:
    return {
        "contract_version": "cost-summary-v1",
        "episode_id": "episode-001",
        "attempt_id": "attempt-001",
        "method_condition": "M0",
        "source_event_ids": ["attempt-event-" + HASH],
        "source_events_sha256": HASH,
        "event_count": 1,
        "failure_count": 0,
        "budget_exhaustion_count": 0,
        "accounting_closed": True,
        "all_required_axes_reconciled": True,
        "axes": {
            axis: {"status": "measured", "value": 0, "reason": None}
            for axis in AXES
        },
    }


def test_accounting_contracts_accept_closed_full_axis_shapes() -> None:
    _validator("contracts/accounting/attempt-event-v1.schema.json").validate(
        _close_event()
    )
    _validator("contracts/accounting/cost-summary-v1.schema.json").validate(
        _summary()
    )


def test_attempt_event_rejects_incomplete_close_and_raw_extra_fields() -> None:
    validator = _validator("contracts/accounting/attempt-event-v1.schema.json")
    incomplete = copy.deepcopy(_close_event())
    incomplete["cost_delta"].pop("eda_time")
    with pytest.raises(ValidationError):
        validator.validate(incomplete)

    leaked = copy.deepcopy(_close_event())
    leaked["stdout"] = "private tool output"
    with pytest.raises(ValidationError):
        validator.validate(leaked)


def test_cost_summary_preserves_unavailable_instead_of_zero() -> None:
    validator = _validator("contracts/accounting/cost-summary-v1.schema.json")
    unavailable = _summary()
    unavailable["all_required_axes_reconciled"] = False
    unavailable["axes"]["input_tokens"] = {
        "status": "unavailable",
        "value": None,
        "reason": "provider_usage_missing",
    }
    with pytest.raises(ValidationError):
        validator.validate(unavailable | {"all_required_axes_reconciled": True})
    validator.validate(unavailable)

    unavailable["axes"]["input_tokens"]["value"] = 0
    with pytest.raises(ValidationError):
        validator.validate(unavailable)
