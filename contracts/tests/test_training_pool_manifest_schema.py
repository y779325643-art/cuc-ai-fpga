import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/training-release/training-pool-manifest-v1.schema.json").read_text(
        encoding="utf-8"
    )
)


def _ref(treatment):
    ref = {
        "source_episode_id": "episode-001",
        "treatment": treatment,
        "row_id": f"row-{treatment}",
        "row_sha256": "a" * 64,
        "sidecar_artifact_sha256": "b" * 64,
        "eligibility_artifact_sha256": "c" * 64,
    }
    if treatment in {"M6T", "M6F_E_TRAJ"}:
        ref["transition_evidence_sha256"] = "d" * 64
    return ref


def _manifest():
    return {
        "contract_version": "training-pool-manifest-v1",
        "artifact_sha256": "0" * 64,
        "visibility_class": "release_internal",
        "pool_id": "pool-001",
        "policy_id": "policy-001",
        "policy_sha256": "1" * 64,
        "training_split_id": "train-split-dev",
        "e_final_episode_ids": ["episode-001"],
        "e_final_set_sha256": "2" * 64,
        "e_traj_episode_ids": ["episode-001"],
        "e_traj_set_sha256": "3" * 64,
        "treatment_rows": {
            treatment: [_ref(treatment)]
            for treatment in ("M6U", "M6F", "M6T", "M6F_E_TRAJ")
        },
        "mixture_strata": [
            {
                "family_id": "counter",
                "source_class": "model_generated",
                "failure_origin": "natural_llm",
                "episode_ids": ["episode-001"],
                "episode_count": 1,
            }
        ],
    }


def _errors(payload):
    return tuple(Draft202012Validator(SCHEMA).iter_errors(payload))


def test_training_pool_manifest_schema_accepts_canonical_shape() -> None:
    assert _errors(_manifest()) == ()


def test_training_pool_manifest_schema_is_closed() -> None:
    payload = _manifest()
    payload["signed_release"] = True
    assert _errors(payload)


def test_training_pool_manifest_requires_transition_hash_only_for_traj_rows() -> None:
    missing = _manifest()
    del missing["treatment_rows"]["M6T"][0]["transition_evidence_sha256"]
    assert _errors(missing)

    unexpected = copy.deepcopy(_manifest())
    unexpected["treatment_rows"]["M6F"][0]["transition_evidence_sha256"] = "d" * 64
    assert _errors(unexpected)
