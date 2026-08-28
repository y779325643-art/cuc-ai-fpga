import json
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "contracts" / "episode-pack" / "episode-pack-v1.schema.json"


def _payload() -> dict:
    return {
        "contract_version": "episode-pack-v1",
        "pack_id": "pack-001",
        "pack_sha256": "a" * 64,
        "public_context": {
            "requirement_id": "req-001",
            "revision_id": "rev-001",
            "public_text": "Build an 8-bit counter.",
            "fact_records": [
                {
                    "fact_id": "data_width_bits",
                    "value": 8,
                    "provenance": "user_explicit",
                    "source_ids": ["text:8-bit"],
                }
            ],
            "platform_profile_id": "platform:generic_verilog",
            "platform_profile_sha256": "b" * 64,
            "capability_profile_id": "capability:backend-v1",
            "capability_profile_sha256": "c" * 64,
            "disposition": "ready",
            "public_projection_sha256": "d" * 64,
        },
        "audit_only": {
            "episode_id": "episode-001",
            "analysis_population": "development",
            "method_condition_id": "M0",
            "evaluator_metadata_sha256": "e" * 64,
            "private_ref_ids": ["oracle:opaque-001"],
        },
    }


def test_episode_pack_schema_is_valid_and_accepts_closed_fixture() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)

    assert list(Draft202012Validator(schema).iter_errors(_payload())) == []


def test_generation_visible_context_rejects_evaluator_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = _payload()
    payload["public_context"]["family_id"] = "hidden-family"

    errors = list(Draft202012Validator(schema).iter_errors(payload))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_episode_pack_accepts_paired_block_ref_only_in_audit_projection() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    paired_ref = {
        "key": "paired-blocks/block-" + "1" * 64,
        "sha256": "2" * 64,
        "size_bytes": 512,
        "media_type": "application/json",
    }
    payload = _payload()
    payload["audit_only"]["paired_block_ref"] = paired_ref

    assert list(validator.iter_errors(payload)) == []

    leaked = _payload()
    leaked["public_context"]["paired_block_ref"] = paired_ref
    assert list(validator.iter_errors(leaked))


def test_episode_pack_rejects_malformed_paired_block_ref() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = _payload()
    payload["audit_only"]["paired_block_ref"] = {
        "key": "paired-blocks/block-001",
        "sha256": "not-a-hash",
        "size_bytes": 0,
        "media_type": "text/plain",
    }

    assert list(Draft202012Validator(schema).iter_errors(payload))
