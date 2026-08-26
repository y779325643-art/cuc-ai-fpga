import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts" / "accounting" / "development-provider-seed-capability-v1.schema.json"


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _best_effort_payload() -> dict:
    return {
        "contract_version": "development-provider-seed-capability-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "capability_profile_id": "seedcap-" + "a" * 32,
        "provider_adapter": "openai_compatible",
        "provider_model": "gpt-4o-mini-2024-07-18",
        "gateway_base_url_sha256": "b" * 64,
        "probe_protocol": {
            "prompt_sha256": "1" * 64,
            "seed": 17,
            "temperature": 0.1,
            "max_tokens": 32,
            "repetitions": 3,
            "probe_implementation_sha256": "2" * 64,
        },
        "probe_protocol_sha256": "c" * 64,
        "documentation_status": "best_effort_documented",
        "documentation_snapshot_sha256": "d" * 64,
        "documentation_source_url_sha256": "f" * 64,
        "documentation_review": {
            "review_type": "self_reviewed_development",
            "reviewer_provenance_sha256": "3" * 64,
        },
        "observations": [
            {
                "call_index": index,
                "status": "completed",
                "output_size_bytes": 15,
                "output_sha256": "e" * 64,
                "system_fingerprint": "fp-a",
                "input_tokens": 8,
                "output_tokens": 4,
                "cached_tokens": 0,
                "failure_category": None,
            }
            for index in range(3)
        ],
        "requested_decoding_seed": 17,
        "planned_repetitions": 3,
        "completed_repetitions": 3,
        "failed_repetitions": 0,
        "failure_categories": [],
        "probe_status": "complete",
        "output_sha256s": ["e" * 64, "e" * 64, "e" * 64],
        "system_fingerprints": ["fp-a", "fp-a", "fp-a"],
        "exact_output_match": True,
        "fingerprint_status": "consistent",
        "fingerprint_match": True,
        "provider_token_usage_status": "provider_reported",
        "input_tokens": 24,
        "output_tokens": 12,
        "cached_tokens": 0,
        "seed_control_classification": "best_effort_observed",
        "paired_confirmatory_eligible": False,
        "limitations": [
            "best_effort_not_guaranteed",
            "documentation_self_reviewed",
            "independent_documentation_review_required",
            "development_only_no_campaign_authority"
        ],
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False
    }


def test_best_effort_observation_validates_without_eligibility() -> None:
    _validator().validate(_best_effort_payload())


def test_best_effort_documentation_cannot_claim_confirmatory_eligibility() -> None:
    payload = _best_effort_payload()
    payload["paired_confirmatory_eligible"] = True

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    "field",
    ("official_outcome", "official_authority", "pass_credit_authority", "g3_accepted", "g4b_authorized"),
)
def test_capability_artifact_rejects_authority_escalation(field: str) -> None:
    payload = copy.deepcopy(_best_effort_payload())
    payload[field] = True

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_infrastructure_error_requires_failure_category() -> None:
    payload = _best_effort_payload()
    payload.update(
        {
            "completed_repetitions": 0,
            "failed_repetitions": 1,
            "failure_categories": [],
            "probe_status": "infrastructure_error",
            "observations": [
                {
                    "call_index": 0,
                    "status": "failed",
                    "output_size_bytes": None,
                    "output_sha256": None,
                    "system_fingerprint": None,
                    "input_tokens": None,
                    "output_tokens": None,
                    "cached_tokens": None,
                    "failure_category": "unknown",
                }
            ],
            "output_sha256s": [],
            "system_fingerprints": [],
            "exact_output_match": None,
            "fingerprint_status": "not_evaluated",
            "fingerprint_match": None,
            "provider_token_usage_status": "unavailable",
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
            "seed_control_classification": "unavailable",
            "limitations": [
                "best_effort_not_guaranteed",
                "probe_not_complete",
                "development_only_no_campaign_authority",
            ],
        }
    )

    with pytest.raises(ValidationError):
        _validator().validate(payload)
