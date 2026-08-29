import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "contracts"
    / "episode-pack"
    / "development-shared-checkpoint-manifest-v1.schema.json"
)
HASH = "a" * 64


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


def _node(checkpoint_id: str) -> dict:
    parents = {
        "direct_initial_project": [],
        "shared_system_his": [],
        "skeleton_initial_project": ["shared_system_his"],
    }
    consumers = {
        "direct_initial_project": ["M0", "M1"],
        "shared_system_his": ["M3", "M4", "M5"],
        "skeleton_initial_project": ["M4", "M5"],
    }
    project = checkpoint_id != "shared_system_his"
    artifact_key = {
        "direct_initial_project": "checkpoints/direct-initial-project",
        "shared_system_his": "checkpoints/system-his",
        "skeleton_initial_project": "checkpoints/skeleton-initial-project",
    }[checkpoint_id]
    return {
        "checkpoint_id": checkpoint_id,
        "status": "completed",
        "reason": None,
        "artifact_ref": _ref(artifact_key),
        "content_sha256": HASH,
        "project_package_sha256": HASH if project else None,
        "trusted_skeleton_ref": (
            _ref("checkpoints/trusted-skeleton")
            if checkpoint_id == "skeleton_initial_project"
            else None
        ),
        "parent_checkpoint_ids": parents[checkpoint_id],
        "consumer_methods": consumers[checkpoint_id],
        "source_event_refs": [_ref(f"events/{checkpoint_id}")],
        "source_events_sha256": HASH,
    }


def _complete_manifest() -> dict:
    return {
        "contract_version": "development-shared-checkpoint-manifest-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_ref": _ref("paired-blocks/block-" + HASH),
        "preparation_policy_sha256": HASH,
        "manifest_status": "complete",
        "nodes": [
            _node("direct_initial_project"),
            _node("shared_system_his"),
            _node("skeleton_initial_project"),
        ],
        "block_event_refs": [_ref("events/close")],
        "block_events_sha256": HASH,
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }


def test_manifest_requires_exact_checkpoint_graph() -> None:
    _validator().validate(_complete_manifest())

    wrong = copy.deepcopy(_complete_manifest())
    wrong["nodes"][2]["parent_checkpoint_ids"] = []
    with pytest.raises(ValidationError):
        _validator().validate(wrong)


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
def test_manifest_rejects_authority_escalation(field: str) -> None:
    payload = _complete_manifest()
    payload[field] = True

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_manifest_requires_checkpoint_artifact_key_suffixes() -> None:
    direct = _complete_manifest()
    direct["nodes"][0]["artifact_ref"]["key"] = "checkpoints/wrong"
    his = _complete_manifest()
    his["nodes"][1]["artifact_ref"]["key"] = "checkpoints/wrong"
    skeleton = _complete_manifest()
    skeleton["nodes"][2]["artifact_ref"]["key"] = "checkpoints/wrong"

    for payload in (direct, his, skeleton):
        with pytest.raises(ValidationError):
            _validator().validate(payload)


def test_manifest_rejects_wrong_consumers_cycle_and_missing_event_refs() -> None:
    wrong_consumers = _complete_manifest()
    wrong_consumers["nodes"][0]["consumer_methods"] = ["M0"]
    cycle = _complete_manifest()
    cycle["nodes"][0]["parent_checkpoint_ids"] = ["skeleton_initial_project"]
    missing_events = _complete_manifest()
    missing_events["nodes"][1]["source_event_refs"] = []

    for payload in (wrong_consumers, cycle, missing_events):
        with pytest.raises(ValidationError):
            _validator().validate(payload)


def test_manifest_requires_completed_artifacts_and_keeps_incomplete_refs_null() -> None:
    missing_completed = _complete_manifest()
    missing_completed["nodes"][0]["artifact_ref"] = None
    incomplete = _complete_manifest()
    incomplete["manifest_status"] = "incomplete"
    incomplete["nodes"][2].update(
        {
            "status": "not_run",
            "reason": "blocked_by_shared_checkpoint",
            "artifact_ref": None,
            "content_sha256": None,
            "project_package_sha256": None,
            "trusted_skeleton_ref": None,
        }
    )
    invalid_incomplete = copy.deepcopy(incomplete)
    invalid_incomplete["nodes"][2]["artifact_ref"] = _ref("checkpoints/illegal")

    with pytest.raises(ValidationError):
        _validator().validate(missing_completed)
    _validator().validate(incomplete)
    with pytest.raises(ValidationError):
        _validator().validate(invalid_incomplete)


def test_manifest_rejects_trusted_skeleton_substitution_and_unknown_fields() -> None:
    substituted = _complete_manifest()
    substituted["nodes"][2]["artifact_ref"] = substituted["nodes"][2]["trusted_skeleton_ref"]
    unknown = _complete_manifest()
    unknown["nodes"][0]["private_trace"] = True

    with pytest.raises(ValidationError):
        _validator().validate(substituted)
    with pytest.raises(ValidationError):
        _validator().validate(unknown)
