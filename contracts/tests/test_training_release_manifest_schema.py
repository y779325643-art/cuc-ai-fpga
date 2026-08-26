import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (
        ROOT / "contracts/training-release/training-release-manifest-v1.schema.json"
    ).read_text(encoding="utf-8")
)


def _manifest(state="candidate_unpromoted"):
    treatments = []
    for treatment in ("M6U", "M6F", "M6T", "M6F_E_TRAJ"):
        treatments.append(
            {
                "treatment": treatment,
                "view_path": f"views/{treatment}.jsonl",
                "view_sha256": "a" * 64,
                "row_count": 1,
                "episode_set_sha256": "b" * 64,
                "row_set_sha256": "c" * 64,
            }
        )
    payload = {
        "contract_version": "training-release-manifest-v1",
        "artifact_sha256": "0" * 64,
        "visibility_class": "public",
        "release_id": "release-001",
        "release_state": state,
        "training_authorized": state == "promoted",
        "pool_id": "pool-001",
        "pool_manifest_path": "internal/training-pool-manifest.json",
        "pool_manifest_sha256": "1" * 64,
        "training_split_id": "train-split-dev",
        "e_final_set_sha256": "2" * 64,
        "e_traj_set_sha256": "3" * 64,
        "official_hidden_outcome_reference_count": 0,
        "leakage_audit": {
            "policy_id": "leakage-policy-001",
            "policy_sha256": "4" * 64,
            "forbidden_canary_set_sha256": "5" * 64,
            "status": "pass",
        },
        "treatments": treatments,
        "release_files": [
            {
                "path": "views/M6U.jsonl",
                "sha256": "a" * 64,
                "size_bytes": 100,
                "role": "training_view",
                "visibility_class": "model_visible",
            }
        ],
    }
    if state == "promoted":
        payload["authorization"] = {
            "campaign_freeze_sha256": "6" * 64,
            "training_plan_sha256": "7" * 64,
            "promotion_record_sha256": "8" * 64,
        }
    return payload


def _errors(payload):
    return tuple(Draft202012Validator(SCHEMA).iter_errors(payload))


def test_training_release_schema_distinguishes_candidate_and_promoted() -> None:
    assert _errors(_manifest()) == ()
    assert _errors(_manifest("promoted")) == ()


def test_candidate_cannot_authorize_training_or_carry_authorization() -> None:
    candidate = _manifest()
    candidate["training_authorized"] = True
    candidate["authorization"] = {
        "campaign_freeze_sha256": "6" * 64,
        "training_plan_sha256": "7" * 64,
        "promotion_record_sha256": "8" * 64,
    }
    assert _errors(candidate)


def test_training_release_schema_is_closed() -> None:
    payload = copy.deepcopy(_manifest())
    payload["raw_hidden_outcome"] = "pass"
    assert _errors(payload)
