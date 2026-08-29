"""Verified development-only shared-checkpoint manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, Mapping

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.block_cost_accounting import replay_development_block_preparation
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.paired_block import load_development_paired_block
from sr2fpga_agent.project_contract import project_package_sha256

if TYPE_CHECKING:
    from sr2fpga_agent.method_adapters import (
        PlanningArtifactEmission,
        ProjectCandidateEmission,
    )


class CheckpointId(str, Enum):
    DIRECT_INITIAL_PROJECT = "direct_initial_project"
    SHARED_SYSTEM_HIS = "shared_system_his"
    SKELETON_INITIAL_PROJECT = "skeleton_initial_project"


_CHECKPOINT_SUFFIX = {
    CheckpointId.DIRECT_INITIAL_PROJECT: "direct-initial-project",
    CheckpointId.SHARED_SYSTEM_HIS: "system-his",
    CheckpointId.SKELETON_INITIAL_PROJECT: "skeleton-initial-project",
}
_PARENTS = {
    CheckpointId.DIRECT_INITIAL_PROJECT: (),
    CheckpointId.SHARED_SYSTEM_HIS: (),
    CheckpointId.SKELETON_INITIAL_PROJECT: (CheckpointId.SHARED_SYSTEM_HIS,),
}
_CONSUMERS = {
    CheckpointId.DIRECT_INITIAL_PROJECT: ("M0", "M1"),
    CheckpointId.SHARED_SYSTEM_HIS: ("M3", "M4", "M5"),
    CheckpointId.SKELETON_INITIAL_PROJECT: ("M4", "M5"),
}


@dataclass(frozen=True)
class CheckpointNode:
    checkpoint_id: CheckpointId
    status: str
    reason: str | None
    artifact_ref: ArtifactRef | None
    content_sha256: str | None
    project_package_sha256: str | None
    trusted_skeleton_ref: ArtifactRef | None
    parent_checkpoint_ids: tuple[CheckpointId, ...]
    consumer_methods: tuple[str, ...]
    source_event_refs: tuple[ArtifactRef, ...]
    source_events_sha256: str


@dataclass(frozen=True)
class PreparedBlockArtifacts:
    paired_block_ref: ArtifactRef
    manifest_ref: ArtifactRef
    direct_initial_project: ProjectCandidateEmission | None
    system_his: PlanningArtifactEmission | None
    skeleton_initial_project: ProjectCandidateEmission | None
    trusted_skeleton: ProjectCandidateEmission | None
    event_refs: tuple[ArtifactRef, ...]


def write_development_shared_checkpoint_manifest(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    preparation_policy_sha256: str,
    nodes: Iterable[CheckpointNode],
    block_event_refs: Iterable[ArtifactRef],
) -> ArtifactRef:
    """Persist a closed shared-checkpoint DAG backed by Task 1 raw events."""

    _require_store_reference(store, paired_block_ref, "paired block")
    load_development_paired_block(store, paired_block_ref)
    _require_sha256(preparation_policy_sha256, "preparation policy")
    event_refs = tuple(block_event_refs)
    replay = replay_development_block_preparation(store, event_refs)
    if replay.paired_block_ref != paired_block_ref:
        raise ValueError("block preparation events name another paired block")
    node_records = tuple(nodes)
    _validate_nodes(store, node_records, replay.events, replay.event_refs)
    payload = {
        "contract_version": "development-shared-checkpoint-manifest-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_ref": paired_block_ref.to_dict(),
        "preparation_policy_sha256": preparation_policy_sha256,
        "manifest_status": (
            "complete" if all(node.status == "completed" for node in node_records) else "incomplete"
        ),
        "nodes": [_node_payload(node) for node in node_records],
        "block_event_refs": [reference.to_dict() for reference in replay.event_refs],
        "block_events_sha256": _event_set_sha256(store, replay.event_refs),
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    return store.put_validated_json(
        f"shared-checkpoint-manifests/{paired_block_ref.sha256}/{preparation_policy_sha256}",
        payload,
        contract_key="development_shared_checkpoint_manifest",
    )


def read_development_shared_checkpoint_manifest(
    store: ArtifactStore, reference: ArtifactRef
) -> dict[str, Any]:
    """Read and revalidate every graph, event, and completed artifact binding."""

    try:
        payload = json.loads(store.read_verified(reference))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("shared checkpoint manifest is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("shared checkpoint manifest must be a JSON object")
    errors = ContractRegistry().load_schema("development_shared_checkpoint_manifest").validate(
        payload
    )
    if errors:
        raise ValueError("invalid shared checkpoint manifest: " + "; ".join(errors))
    paired_block_ref = _artifact_ref(payload["paired_block_ref"])
    _require_store_reference(store, paired_block_ref, "paired block")
    load_development_paired_block(store, paired_block_ref)
    _require_sha256(payload["preparation_policy_sha256"], "preparation policy")
    event_refs = tuple(_artifact_ref(item) for item in payload["block_event_refs"])
    replay = replay_development_block_preparation(store, event_refs)
    if replay.paired_block_ref != paired_block_ref:
        raise ValueError("manifest and block preparation paired blocks differ")
    if payload["block_events_sha256"] != _event_set_sha256(store, replay.event_refs):
        raise ValueError("manifest block event-set digest mismatch")
    nodes = tuple(_node_from_payload(item) for item in payload["nodes"])
    _validate_nodes(store, nodes, replay.events, replay.event_refs)
    expected_status = "complete" if all(node.status == "completed" for node in nodes) else "incomplete"
    if payload["manifest_status"] != expected_status:
        raise ValueError("manifest status does not match checkpoint statuses")
    return payload


def _validate_nodes(
    store: ArtifactStore,
    nodes: tuple[CheckpointNode, ...],
    events: tuple[dict[str, Any], ...],
    event_refs: tuple[ArtifactRef, ...],
) -> None:
    if len(nodes) != len(CheckpointId) or {node.checkpoint_id for node in nodes} != set(CheckpointId):
        raise ValueError("shared checkpoint manifest must contain exactly the checkpoint DAG")
    partitions = {
        checkpoint: tuple(
            reference
            for reference, event in zip(event_refs, events, strict=True)
            if event["checkpoint_id"] == checkpoint.value
        )
        for checkpoint in CheckpointId
    }
    nodes_by_id = {node.checkpoint_id: node for node in nodes}
    direct = nodes_by_id[CheckpointId.DIRECT_INITIAL_PROJECT]
    skeleton = nodes_by_id[CheckpointId.SKELETON_INITIAL_PROJECT]
    if (
        direct.artifact_ref is not None
        and direct.artifact_ref == skeleton.artifact_ref
    ):
        raise ValueError("direct and skeleton checkpoint artifacts must be distinct")
    for node in nodes:
        if node.parent_checkpoint_ids != _PARENTS[node.checkpoint_id]:
            raise ValueError("checkpoint parent graph mismatch")
        if node.consumer_methods != _CONSUMERS[node.checkpoint_id]:
            raise ValueError("checkpoint consumer set mismatch")
        if not node.source_event_refs:
            raise ValueError("checkpoint source event set is empty")
        if node.source_event_refs != partitions[node.checkpoint_id]:
            raise ValueError("checkpoint source event partition mismatch")
        if node.source_events_sha256 != _event_set_sha256(store, node.source_event_refs):
            raise ValueError("checkpoint source event-set digest mismatch")
        partition_events = tuple(
            event for event in events if event["checkpoint_id"] == node.checkpoint_id.value
        )
        _validate_node_artifacts(store, node, partition_events)


def _validate_node_artifacts(
    store: ArtifactStore, node: CheckpointNode, events: tuple[dict[str, Any], ...]
) -> None:
    if node.status not in {"completed", "failed", "not_run"}:
        raise ValueError("checkpoint status is invalid")
    terminal = [
        event
        for event in events
        if event["event_kind"]
        in {"checkpoint_materialized", "checkpoint_failed", "checkpoint_not_run"}
    ]
    expected_event_kind = {
        "completed": "checkpoint_materialized",
        "failed": "checkpoint_failed",
        "not_run": "checkpoint_not_run",
    }[node.status]
    if (
        len(terminal) != 1
        or terminal[0]["event_kind"] != expected_event_kind
        or terminal[0]["status"] != node.status
        or terminal[0]["reason"] != node.reason
    ):
        raise ValueError("checkpoint terminal event does not match manifest node")
    if node.status != "completed":
        if node.reason is None or any(
            value is not None
            for value in (
                node.artifact_ref,
                node.content_sha256,
                node.project_package_sha256,
                node.trusted_skeleton_ref,
            )
        ):
            raise ValueError("incomplete checkpoint fields must be null with a reason")
        return
    if node.reason is not None or node.artifact_ref is None or node.content_sha256 is None:
        raise ValueError("completed checkpoint needs artifact content and no reason")
    _require_store_reference(store, node.artifact_ref, "checkpoint artifact")
    _require_checkpoint_artifact_key(node)
    content = store.read_verified(node.artifact_ref)
    if node.content_sha256 != hashlib.sha256(content).hexdigest():
        raise ValueError("checkpoint content digest mismatch")
    output_refs = tuple(_artifact_ref(item) for item in terminal[0]["output_artifact_refs"])
    if node.artifact_ref not in output_refs:
        raise ValueError("completed checkpoint artifact is absent from raw event")
    if node.checkpoint_id is CheckpointId.SHARED_SYSTEM_HIS:
        if node.project_package_sha256 is not None or node.trusted_skeleton_ref is not None:
            raise ValueError("System-HIS checkpoint has project-only fields")
        try:
            planning = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("System-HIS checkpoint content is not valid JSON") from exc
        if not isinstance(planning, dict):
            raise ValueError("System-HIS checkpoint content must be a JSON object")
        return
    if node.project_package_sha256 is None:
        raise ValueError("project checkpoint needs a package digest")
    _verify_project_digest(content, node.project_package_sha256, "checkpoint project")
    if node.checkpoint_id is CheckpointId.DIRECT_INITIAL_PROJECT:
        if node.trusted_skeleton_ref is not None:
            raise ValueError("direct checkpoint has a trusted skeleton")
        return
    if node.trusted_skeleton_ref is None:
        raise ValueError("skeleton checkpoint needs a trusted skeleton artifact")
    if node.trusted_skeleton_ref == node.artifact_ref:
        raise ValueError("trusted skeleton cannot substitute the complete project")
    _require_store_reference(store, node.trusted_skeleton_ref, "trusted skeleton")
    if node.trusted_skeleton_ref not in output_refs:
        raise ValueError("trusted skeleton is absent from raw event")
    _verify_project_digest(
        store.read_verified(node.trusted_skeleton_ref),
        None,
        "trusted skeleton",
    )


def _verify_project_digest(content: bytes, expected: str | None, label: str) -> None:
    try:
        payload = json.loads(content)
        project = GeneratedProject(str(payload["project_name"]), dict(payload["files"]))
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not a project artifact") from exc
    actual = project_package_sha256(project)
    if expected is not None and expected != actual:
        raise ValueError(f"{label} package digest mismatch")


def _require_checkpoint_artifact_key(node: CheckpointNode) -> None:
    if node.artifact_ref is None:
        raise ValueError("completed checkpoint needs an artifact key")
    suffix = _CHECKPOINT_SUFFIX[node.checkpoint_id]
    if not node.artifact_ref.key.endswith(f"/{suffix}"):
        raise ValueError(f"checkpoint artifact key must end with /{suffix}")


def _node_payload(node: CheckpointNode) -> dict[str, Any]:
    return {
        "checkpoint_id": node.checkpoint_id.value,
        "status": node.status,
        "reason": node.reason,
        "artifact_ref": None if node.artifact_ref is None else node.artifact_ref.to_dict(),
        "content_sha256": node.content_sha256,
        "project_package_sha256": node.project_package_sha256,
        "trusted_skeleton_ref": (
            None if node.trusted_skeleton_ref is None else node.trusted_skeleton_ref.to_dict()
        ),
        "parent_checkpoint_ids": [value.value for value in node.parent_checkpoint_ids],
        "consumer_methods": list(node.consumer_methods),
        "source_event_refs": [reference.to_dict() for reference in node.source_event_refs],
        "source_events_sha256": node.source_events_sha256,
    }


def _node_from_payload(payload: Mapping[str, Any]) -> CheckpointNode:
    return CheckpointNode(
        checkpoint_id=CheckpointId(payload["checkpoint_id"]),
        status=payload["status"],
        reason=payload["reason"],
        artifact_ref=None if payload["artifact_ref"] is None else _artifact_ref(payload["artifact_ref"]),
        content_sha256=payload["content_sha256"],
        project_package_sha256=payload["project_package_sha256"],
        trusted_skeleton_ref=(
            None
            if payload["trusted_skeleton_ref"] is None
            else _artifact_ref(payload["trusted_skeleton_ref"])
        ),
        parent_checkpoint_ids=tuple(CheckpointId(item) for item in payload["parent_checkpoint_ids"]),
        consumer_methods=tuple(payload["consumer_methods"]),
        source_event_refs=tuple(_artifact_ref(item) for item in payload["source_event_refs"]),
        source_events_sha256=payload["source_events_sha256"],
    )


def _artifact_ref(payload: Mapping[str, Any]) -> ArtifactRef:
    return ArtifactRef(
        key=payload["key"],
        sha256=payload["sha256"],
        size_bytes=payload["size_bytes"],
        media_type=payload["media_type"],
    )


def _event_set_sha256(store: ArtifactStore, references: Iterable[ArtifactRef]) -> str:
    ids = []
    for reference in references:
        event = json.loads(store.read_verified(reference))
        event_id = event.get("event_id") if isinstance(event, dict) else None
        if not isinstance(event_id, str):
            raise ValueError("checkpoint event has no event ID")
        ids.append(event_id)
    return hashlib.sha256(_canonical_json(ids)).hexdigest()


def _require_store_reference(store: ArtifactStore, reference: ArtifactRef, label: str) -> None:
    if store.reference(reference.key) != reference:
        raise ValueError(f"{label} reference does not match its immutable key")
    store.read_verified(reference)


def _require_sha256(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be SHA-256") from exc


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
