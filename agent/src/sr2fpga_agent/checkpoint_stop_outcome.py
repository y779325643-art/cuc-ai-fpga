"""Registered, replayable no-candidate outcomes for failed shared preparation."""

from __future__ import annotations

import hashlib
import json

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.block_preparation import (
    blocked_methods_from_verified_manifest,
    read_development_shared_checkpoint_manifest,
)
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.frozen_context import validate_episode_pack
from sr2fpga_agent.paired_block import load_development_paired_block


def reconcile_checkpoint_stop_outcome(
    store: ArtifactStore, *, episode_pack_ref: ArtifactRef, checkpoint_manifest_ref: ArtifactRef,
) -> tuple[dict, ArtifactRef]:
    pack = json.loads(store.read_verified(episode_pack_ref))
    errors = validate_episode_pack(pack)
    if errors:
        raise ValueError("checkpoint stop has invalid episode pack: " + "; ".join(errors))
    audit = pack["audit_only"]
    if audit["analysis_population"] not in {"development", "excluded"}:
        raise ValueError("checkpoint stop cannot create official outcomes")
    manifest = read_development_shared_checkpoint_manifest(store, checkpoint_manifest_ref)
    if audit.get("paired_block_ref") != manifest["paired_block_ref"]:
        raise ValueError("checkpoint stop episode belongs to a different paired block")
    block = load_development_paired_block(store, ArtifactRef(**manifest["paired_block_ref"]))
    if pack["public_context"]["public_projection_sha256"] != block["public_projection_sha256"]:
        raise ValueError("checkpoint stop public requirement projection mismatch")
    method = audit["method_condition_id"]
    blocked = blocked_methods_from_verified_manifest(store, checkpoint_manifest_ref)
    if method not in blocked:
        raise ValueError("method is not blocked by shared preparation")
    checkpoint = blocked[method]
    node = next(item for item in manifest["nodes"] if item["checkpoint_id"] == checkpoint)
    events = [json.loads(store.read_verified(ArtifactRef(**raw))) for raw in node["source_event_refs"]]
    completed_calls = any(event["event_kind"] == "axis_cost" and event["status"] == "completed" for event in events)
    failed_calls = any(event["event_kind"] == "axis_cost" and event["status"] == "failed" for event in events)
    integrity_violation = str(node["reason"]).split(":", 1)[0] in {
        "ArtifactIntegrityError", "ArtifactConflictError", "OneShotViolation",
    }
    design_failure = completed_calls and not failed_calls and not integrity_violation
    payload = {
        "contract_version": "development-checkpoint-stop-outcome-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "episode_id": audit["episode_id"], "method_condition": method,
        "analysis_population": audit["analysis_population"],
        "episode_pack_ref": episode_pack_ref.to_dict(),
        "checkpoint_manifest_ref": checkpoint_manifest_ref.to_dict(),
        "paired_block_ref": manifest["paired_block_ref"],
        "semantic_instance_id": block["semantic_instance_id"],
        "replicate_id": block["replicate_id"], "paired_block_id": block["paired_block_id"],
        "blocked_checkpoint_id": checkpoint,
        "checkpoint_failure_reason": (
            "dependency_failed" if node["status"] == "not_run" else "shared_preparation_failed"
        ),
        "execution_status": "not_run",
        "semantic_status": "design_failure" if design_failure else "not_evaluated",
        "development_vpp_l3": False if design_failure else None,
        "integrity_violation": integrity_violation,
        "hidden_execution_status": "not_run", "hidden_semantic_status": None,
        "semantic_commit_count": 0,
        "terminal_candidate_ref": None,
        "block_event_refs": manifest["block_event_refs"],
        "denominator": {"retained": True, "replacement_allowed": False},
        "official_outcome": False, "official_authority": False,
        "pass_credit_authority": False, "g3_accepted": False, "g4b_authorized": False,
    }
    payload["outcome_id"] = "checkpoint-stop-" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    reference = store.put_validated_json(
        f"checkpoint-stop-outcomes/{audit['episode_id']}/{method}", payload,
        contract_key="development_checkpoint_stop_outcome",
    )
    return payload, reference


def read_verified_checkpoint_stop_outcome(store: ArtifactStore, reference: ArtifactRef) -> dict:
    payload = json.loads(store.read_verified(reference))
    errors = ContractRegistry().load_schema("development_checkpoint_stop_outcome").validate(payload)
    if errors:
        raise ValueError("invalid checkpoint stop outcome: " + "; ".join(errors))
    rebuilt, rebuilt_ref = reconcile_checkpoint_stop_outcome(
        store, episode_pack_ref=ArtifactRef(**payload["episode_pack_ref"]),
        checkpoint_manifest_ref=ArtifactRef(**payload["checkpoint_manifest_ref"]),
    )
    if rebuilt != payload or rebuilt_ref != reference:
        raise ValueError("checkpoint stop does not match replayed sources")
    return payload
