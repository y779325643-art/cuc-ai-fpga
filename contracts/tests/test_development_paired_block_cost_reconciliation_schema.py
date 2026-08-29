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
    / "development-paired-block-cost-reconciliation-v1.schema.json"
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
METHODS = ("M0", "M1", "M2", "M3", "M4", "M5")
CONTRASTS = (
    ("M1-M0", "direct_initial_project", "M1", "M0"),
    ("M4-M3", "shared_system_his", "M4", "M3"),
    ("M5-M4", "skeleton_initial_project", "M5", "M4"),
)
AUTHORITIES = (
    "official_outcome",
    "official_authority",
    "pass_credit_authority",
    "rq1_evidence",
    "rq2_evidence",
    "g3_accepted",
    "g4b_authorized",
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


def _axes(value: float = 1) -> dict:
    return {
        axis: {"status": "measured", "value": value, "reason": None}
        for axis in AXES
    }


def _method(method: str) -> dict:
    return {
        "method_condition": method,
        "terminal_status": "completed",
        "blocked_checkpoint_id": None,
        "blocked_reason": None,
        "trajectory_ref": _ref(f"trajectories/episode-{method}/{method}"),
        "cost_summary_refs": [_ref(f"cost-summaries/episode-{method}/attempt-000")],
        "attempt_event_refs": [_ref(f"attempt-events/episode-{method}/attempt-000/000000")],
        "source_events_sha256": HASH,
        "exclusive_axes": _axes(),
        "standalone_attributed_axes": _axes(2),
    }


def _contrast(
    contrast_id: str, checkpoint_id: str, treatment: str, baseline: str
) -> dict:
    return {
        "contrast_id": contrast_id,
        "checkpoint_id": checkpoint_id,
        "treatment_method": treatment,
        "baseline_method": baseline,
        "status": "measured",
        "reason": None,
        "arms": [
            {"role": "treatment", "method_condition": treatment, "axes": _axes()},
            {"role": "baseline", "method_condition": baseline, "axes": _axes()},
        ],
        "signed_delta_axes": _axes(0),
    }


def _complete_reconciliation() -> dict:
    return {
        "contract_version": "development-paired-block-cost-reconciliation-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "reconciliation_status": "complete",
        "incomplete_reasons": [],
        "paired_block_ref": _ref("paired-blocks/block-" + HASH),
        "checkpoint_manifest_ref": _ref("shared-checkpoint-manifests/block/policy"),
        "block_event_refs": [_ref("block-events/000000")],
        "source_full_pack_runner_ref": _ref("full-pack-smokes/smoke/runner-v2"),
        "reducer_policy_sha256": HASH,
        "actual_block_axes": _axes(6),
        "method_records": [_method(method) for method in METHODS],
        "incremental_contrasts": [_contrast(*record) for record in CONTRASTS],
        "source_event_partition": {
            "block_event_ids": ["block-preparation-event-" + HASH],
            "block_events_sha256": HASH,
            "method_event_ids": {
                method: ["attempt-event-" + f"{index:02x}" + HASH[:-2]]
                for index, method in enumerate(METHODS)
            },
            "source_events_sha256": HASH,
        },
        "reconciliation": {
            "method_set": list(METHODS),
            "checkpoint_manifest_verified": True,
            "all_source_artifacts_verified": True,
            "all_available_trajectories_verified": True,
            "source_event_partition_disjoint": True,
            "all_required_axes_classified": True,
            "full_pack_lineage_verified": True,
            "all_authority_fields_false": True,
        },
        **{field: False for field in AUTHORITIES},
    }


def _incomplete_reconciliation() -> dict:
    payload = _complete_reconciliation()
    payload["reconciliation_status"] = "incomplete"
    payload["incomplete_reasons"] = [
        "blocked_by_shared_checkpoint:direct_initial_project"
    ]
    payload["source_full_pack_runner_ref"] = None
    payload["reconciliation"]["full_pack_lineage_verified"] = False
    blocked = payload["method_records"][0]
    blocked.update(
        {
            "terminal_status": "blocked_by_shared_checkpoint",
            "blocked_checkpoint_id": "direct_initial_project",
            "blocked_reason": "checkpoint_failed:direct_initial_project",
            "trajectory_ref": None,
            "cost_summary_refs": [],
            "attempt_event_refs": [],
            "exclusive_axes": _axes(0),
        }
    )
    payload["source_event_partition"]["method_event_ids"]["M0"] = []
    affected = payload["incremental_contrasts"][0]
    affected["status"] = "unavailable"
    affected["reason"] = "blocked_by_shared_checkpoint:direct_initial_project"
    affected["signed_delta_axes"] = {
        axis: {
            "status": "unavailable",
            "value": None,
            "reason": "blocked_by_shared_checkpoint:direct_initial_project",
        }
        for axis in AXES
    }
    return payload


def test_complete_and_incomplete_reconciliations_are_valid() -> None:
    _validator().validate(_complete_reconciliation())
    _validator().validate(_incomplete_reconciliation())


def test_signed_delta_allows_negative_measured_value() -> None:
    payload = _complete_reconciliation()
    payload["incremental_contrasts"][0]["signed_delta_axes"]["wall_time"] = {
        "status": "measured",
        "value": -0.5,
        "reason": None,
    }
    _validator().validate(payload)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload["method_records"].pop(),
        lambda payload: payload["incremental_contrasts"].pop(),
        lambda payload: payload["actual_block_axes"].pop("wall_time"),
        lambda payload: payload["method_records"][0]["exclusive_axes"].pop(
            "logical_model_calls"
        ),
        lambda payload: payload["incremental_contrasts"][0]["arms"][0][
            "axes"
        ].pop("eda_time"),
        lambda payload: payload["incremental_contrasts"][0][
            "signed_delta_axes"
        ].pop("cached_tokens"),
    ),
)
def test_reconciliation_requires_all_methods_contrasts_and_axes(mutation) -> None:
    payload = _complete_reconciliation()
    mutation(payload)

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_non_delta_axes_are_non_negative() -> None:
    payload = _complete_reconciliation()
    payload["method_records"][0]["standalone_attributed_axes"]["wall_time"][
        "value"
    ] = -0.5

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    "axis_payload",
    (
        {"status": "unavailable", "value": 0, "reason": "provider_missing"},
        {"status": "unavailable", "value": None, "reason": None},
        {"status": "measured", "value": 0, "reason": "provider_missing"},
    ),
)
def test_axis_missingness_is_not_encoded_as_zero_or_without_reason(axis_payload) -> None:
    payload = _incomplete_reconciliation()
    payload["actual_block_axes"]["input_tokens"] = axis_payload

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_complete_record_requires_trajectories_and_full_pack() -> None:
    missing_trajectory = _complete_reconciliation()
    missing_trajectory["method_records"][0]["trajectory_ref"] = None
    missing_full_pack = _complete_reconciliation()
    missing_full_pack["source_full_pack_runner_ref"] = None

    for payload in (missing_trajectory, missing_full_pack):
        with pytest.raises(ValidationError):
            _validator().validate(payload)


def test_incomplete_record_requires_a_named_reason_and_null_full_pack() -> None:
    missing_reason = _incomplete_reconciliation()
    missing_reason["incomplete_reasons"] = []
    unexpected_full_pack = _incomplete_reconciliation()
    unexpected_full_pack["source_full_pack_runner_ref"] = _ref("full-pack/unexpected")

    for payload in (missing_reason, unexpected_full_pack):
        with pytest.raises(ValidationError):
            _validator().validate(payload)


@pytest.mark.parametrize("field", AUTHORITIES)
def test_reconciliation_rejects_partial_or_escalated_authority_group(field: str) -> None:
    missing = _complete_reconciliation()
    missing.pop(field)
    escalated = _complete_reconciliation()
    escalated[field] = True

    for payload in (missing, escalated):
        with pytest.raises(ValidationError):
            _validator().validate(payload)


def test_reconciliation_rejects_unknown_fields() -> None:
    payload = copy.deepcopy(_complete_reconciliation())
    payload["private_score"] = 1

    with pytest.raises(ValidationError):
        _validator().validate(payload)
