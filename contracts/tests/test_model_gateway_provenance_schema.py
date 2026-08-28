import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts" / "accounting" / "model-gateway-provenance-v1.schema.json"


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _payload() -> dict:
    return {
        "contract_version": "model-gateway-provenance-v1",
        "provenance_id": "mgp-" + "a" * 32,
        "analysis_population": "excluded",
        "episode_id": "episode-1",
        "method_condition": "M4",
        "call_id": 0,
        "stage": "two_stage",
        "operation": "chat",
        "call_status": "completed",
        "provider_adapter": "openai_compatible",
        "provider_model": "model-a",
        "gateway_base_url_sha256": "b" * 64,
        "requested_decoding_seed": 17,
        "seed_forwarding_status": "forwarded",
        "deterministic_seed_control": "requested_unverified",
        "seed_control_evidence_ref": None,
        "provider_system_fingerprint": "fp_backend",
        "system_fingerprint_status": "reported",
        "pass_credit_authority": False,
        "official_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }


def test_requested_unverified_seed_and_reported_fingerprint_validate() -> None:
    _validator().validate(_payload())


def test_negative_call_id_is_rejected() -> None:
    payload = _payload()
    payload["call_id"] = -1

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_supported_seed_requires_hash_bound_capability_evidence() -> None:
    payload = _payload()
    payload["deterministic_seed_control"] = "supported"

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    "field",
    ("pass_credit_authority", "official_authority", "g3_accepted", "g4b_authorized"),
)
def test_provenance_rejects_authority_escalation(field: str) -> None:
    payload = copy.deepcopy(_payload())
    payload[field] = True

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_missing_seed_cannot_claim_forwarding() -> None:
    payload = _payload()
    payload["requested_decoding_seed"] = None

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_requested_seed_cannot_be_recorded_as_not_requested() -> None:
    payload = _payload()
    payload["seed_forwarding_status"] = "not_requested"

    with pytest.raises(ValidationError):
        _validator().validate(payload)
