import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (
        ROOT
        / "contracts/training-release/training-view-eligibility-sidecar-v1.schema.json"
    ).read_text(encoding="utf-8")
)


def _sidecar(treatment="M6F"):
    payload = {
        "contract_version": "training-view-eligibility-sidecar-v1",
        "artifact_sha256": "a" * 64,
        "visibility_class": "release_internal",
        "row_id": "row-001",
        "row_sha256": "b" * 64,
        "source_episode_id": "episode-001",
        "snapshot_id": "snapshot-final",
        "treatment": treatment,
        "eligibility_artifact_sha256": "c" * 64,
        "eligibility_evidence_bundle_sha256": "d" * 64,
        "snapshot_envelope_sha256": "e" * 64,
    }
    if treatment in {"M6T", "M6F_E_TRAJ"}:
        payload["transition_evidence_sha256"] = "f" * 64
    return payload


def _errors(payload):
    return tuple(Draft202012Validator(SCHEMA).iter_errors(payload))


def test_sidecar_schema_accepts_project_and_transition_links() -> None:
    assert _errors(_sidecar()) == ()
    assert _errors(_sidecar("M6T")) == ()
    assert _errors(_sidecar("M6F_E_TRAJ")) == ()


def test_sidecar_schema_is_closed_and_requires_m6t_transition_hash() -> None:
    unknown = _sidecar()
    unknown["eligibility_reason"] = "pass"
    assert _errors(unknown)

    missing = _sidecar("M6T")
    del missing["transition_evidence_sha256"]
    assert _errors(missing)


def test_non_transition_sidecar_forbids_transition_hash() -> None:
    payload = copy.deepcopy(_sidecar())
    payload["transition_evidence_sha256"] = "f" * 64
    assert _errors(payload)
