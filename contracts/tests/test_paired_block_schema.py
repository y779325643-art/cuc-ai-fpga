import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts" / "episode-pack" / "paired-block-v1.schema.json"


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _payload() -> dict:
    return {
        "contract_version": "paired-block-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_id": "pair-fir-001-replicate-000",
        "semantic_instance_id": "semantic-fir-001",
        "replicate_id": "replicate-000",
        "public_projection_sha256": "1" * 64,
        "model_provenance_sha256": "2" * 64,
        "decoding_control_mode": "stochastic_blocked",
        "requested_decoding_seed": 17,
        "execution_schedule_seed": 991,
        "method_order": ["M0", "M1", "M2", "M3", "M4", "M5"],
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }


def test_canonical_paired_block_validates() -> None:
    _validator().validate(_payload())


def test_stochastic_block_allows_absent_requested_seed() -> None:
    payload = _payload()
    payload["requested_decoding_seed"] = None

    _validator().validate(payload)


def test_documented_seed_control_requires_requested_seed() -> None:
    payload = _payload()
    payload["decoding_control_mode"] = "documented_seed_control"
    payload["requested_decoding_seed"] = None

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    "field",
    (
        "official_outcome",
        "official_authority",
        "pass_credit_authority",
        "g3_accepted",
        "g4b_authorized",
    ),
)
def test_authority_escalation_is_rejected(field: str) -> None:
    payload = _payload()
    payload[field] = True

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("requested_decoding_seed", -1),
        ("execution_schedule_seed", -1),
        ("replicate_id", ""),
        ("semantic_instance_id", ""),
    ),
)
def test_invalid_identity_or_seed_is_rejected(field: str, value) -> None:
    payload = _payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    "method_order",
    (
        ["M0", "M1", "M2", "M3", "M4"],
        ["M0", "M1", "M2", "M3", "M4", "M4"],
        ["M0", "M1", "M2", "M3", "M4", "M9"],
    ),
)
def test_incomplete_duplicate_or_unknown_method_order_is_rejected(
    method_order,
) -> None:
    payload = _payload()
    payload["method_order"] = method_order

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_family_id_cannot_replace_semantic_instance_id() -> None:
    payload = _payload()
    del payload["semantic_instance_id"]
    payload["family_id"] = "fir_filter"

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_unknown_field_and_wrong_version_are_rejected() -> None:
    unknown = _payload()
    unknown["success"] = True
    wrong_version = copy.deepcopy(_payload())
    wrong_version["contract_version"] = "paired-block-v2"

    with pytest.raises(ValidationError):
        _validator().validate(unknown)
    with pytest.raises(ValidationError):
        _validator().validate(wrong_version)


def test_contract_manifest_registers_paired_block() -> None:
    manifest = json.loads(
        (ROOT / "contracts" / "manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["contracts"]["paired_block"] == {
        "version": "paired-block-v1",
        "path": "contracts/episode-pack/paired-block-v1.schema.json",
    }
