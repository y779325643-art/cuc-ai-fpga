"""Verified development-only shared-checkpoint manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, Mapping

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.block_cost_accounting import (
    BlockPreparationCostLedger,
    replay_development_block_preparation,
)
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import COST_AXES
from sr2fpga_agent.frozen_context import platform_profile_sha256
from sr2fpga_agent.models import GeneratedProject, PlatformProfile
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.paired_block import load_development_paired_block
from sr2fpga_agent.project_contract import project_package_sha256

if TYPE_CHECKING:
    from sr2fpga_agent.frozen_context import FrozenRequirementContext
    from sr2fpga_agent.generation.context_direct import FrozenContextDirectProjectFacade
    from sr2fpga_agent.generation.context_his import (
        FrozenContextSystemHisFacade,
        FrozenContextSystemHisValidationFacade,
    )
    from sr2fpga_agent.method_adapters import (
        PairingKey,
        PlanningArtifactEmission,
        ProjectCandidateEmission,
    )


class CheckpointId(str, Enum):
    DIRECT_INITIAL_PROJECT = "direct_initial_project"
    SHARED_SYSTEM_HIS = "shared_system_his"
    SKELETON_INITIAL_PROJECT = "skeleton_initial_project"


class SharedCheckpointResumeError(RuntimeError):
    """A prior shared-checkpoint state cannot be reused safely in place."""


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


@dataclass(frozen=True)
class BlockPreparationFacades:
    direct: FrozenContextDirectProjectFacade
    system_his: FrozenContextSystemHisFacade
    his_validation: FrozenContextSystemHisValidationFacade


def prepare_development_paired_block(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    pairing: PairingKey,
    context: FrozenRequirementContext,
    platform: PlatformProfile,
    facades: BlockPreparationFacades,
    model_budget: ModelCallBudget,
    preparation_policy_sha256: str,
) -> PreparedBlockArtifacts:
    """Eagerly materialize and verify the three shared block checkpoints."""

    from sr2fpga_agent.method_adapters import (
        MethodArtifactGateway,
        PairedArtifactCoordinator,
    )

    paired_block = load_development_paired_block(store, paired_block_ref)
    _require_store_reference(store, paired_block_ref, "paired block")
    if platform_profile_sha256(platform) != context.platform_profile_sha256:
        raise ValueError("PlatformProfile does not match frozen requirement context")
    expected_pairing = {
        "paired_block_id": pairing.paired_block_id,
        "semantic_instance_id": pairing.semantic_instance_id,
        "replicate_id": pairing.replicate_id,
        "public_projection_sha256": context.public_projection_sha256,
        "model_provenance_sha256": pairing.model_provenance_sha256,
        "requested_decoding_seed": pairing.decoding_seed,
    }
    for field, value in expected_pairing.items():
        if paired_block[field] != value:
            raise ValueError(f"paired block {field} does not match preparation identity")
    if pairing.requirement_revision_id != context.revision_id:
        raise ValueError("pairing requirement revision does not match frozen context")
    _require_sha256(preparation_policy_sha256, "preparation policy")
    if model_budget.max_calls != 3:
        raise ValueError("block preparation requires a three-call model budget")
    if model_budget.calls_used != 0:
        raise ValueError("block preparation requires an unused model budget")
    ledger = model_budget.attempt_cost_ledger
    if not isinstance(ledger, BlockPreparationCostLedger):
        raise ValueError("block preparation budget must use its block cost ledger")
    if ledger.store is not store or ledger.paired_block_ref != paired_block_ref:
        raise ValueError("block preparation budget ledger names another store or block")

    coordinator = PairedArtifactCoordinator(store)
    artifacts = MethodArtifactGateway(store)
    states: dict[
        CheckpointId,
        tuple[
            str,
            str | None,
            PlanningArtifactEmission | ProjectCandidateEmission | None,
            ProjectCandidateEmission | None,
        ],
    ] = {}

    direct_id = CheckpointId.DIRECT_INITIAL_PROJECT
    ledger.activate_checkpoint(direct_id.value)
    try:
        direct = coordinator.materialize_project_checkpoint(
            pairing,
            direct_id,
            lambda: facades.direct.emit_project(context),
        )
    except Exception as exc:
        reason = _preparation_failure_reason(exc)
        ledger.record_checkpoint(
            checkpoint_id=direct_id.value,
            event_kind="checkpoint_failed",
            status="failed",
            reason=reason,
        )
        states[direct_id] = ("failed", reason, None, None)
    else:
        ledger.record_checkpoint(
            checkpoint_id=direct_id.value,
            event_kind="checkpoint_materialized",
            status="completed",
            output_refs=(direct.artifact_ref,),
        )
        states[direct_id] = ("completed", None, direct, None)

    his_id = CheckpointId.SHARED_SYSTEM_HIS
    ledger.activate_checkpoint(his_id.value)
    try:
        system_his = coordinator.materialize_system_his_checkpoint(
            pairing,
            lambda: facades.system_his.emit_his(context),
        )
        his_payload = artifacts.read_planning(system_his)
        h_report = facades.his_validation.validate_his(context, his_payload)
        if not isinstance(h_report, Mapping) or h_report.get("passed") is not True:
            raise ValueError("System-HIS did not pass complete H0-H3 validation")
    except Exception as exc:
        reason = _preparation_failure_reason(exc)
        ledger.record_checkpoint(
            checkpoint_id=his_id.value,
            event_kind="checkpoint_failed",
            status="failed",
            reason=reason,
        )
        states[his_id] = ("failed", reason, None, None)
    else:
        ledger.record_checkpoint(
            checkpoint_id=his_id.value,
            event_kind="checkpoint_materialized",
            status="completed",
            output_refs=(system_his.artifact_ref,),
        )
        states[his_id] = ("completed", None, system_his, None)

    project_id = CheckpointId.SKELETON_INITIAL_PROJECT
    ledger.activate_checkpoint(project_id.value)
    if states[his_id][0] != "completed":
        reason = "dependency_failed:shared_system_his"
        ledger.record_checkpoint(
            checkpoint_id=project_id.value,
            event_kind="checkpoint_not_run",
            status="not_run",
            reason=reason,
        )
        states[project_id] = ("not_run", reason, None, None)
    else:
        try:
            skeleton_project = coordinator.materialize_project_checkpoint(
                pairing,
                project_id,
                lambda: facades.system_his.emit_skeleton_project(
                    context, his_payload
                ),
            )
            trusted_project = facades.system_his.last_skeleton_project
            if trusted_project is None:
                raise RuntimeError(
                    "skeleton preparation produced no trusted skeleton evidence"
                )
            trusted_skeleton = artifacts.put_project(
                f"paired/{pairing.digest()}/trusted-skeleton",
                trusted_project,
            )
        except Exception as exc:
            reason = _preparation_failure_reason(exc)
            ledger.record_checkpoint(
                checkpoint_id=project_id.value,
                event_kind="checkpoint_failed",
                status="failed",
                reason=reason,
            )
            states[project_id] = ("failed", reason, None, None)
        else:
            ledger.record_checkpoint(
                checkpoint_id=project_id.value,
                event_kind="checkpoint_materialized",
                status="completed",
                input_refs=(system_his.artifact_ref,),
                output_refs=(
                    skeleton_project.artifact_ref,
                    trusted_skeleton.artifact_ref,
                ),
            )
            states[project_id] = (
                "completed",
                None,
                skeleton_project,
                trusted_skeleton,
            )

    if all(state[0] == "completed" for state in states.values()) and model_budget.calls_used != 3:
        raise RuntimeError("complete block preparation did not consume exactly three model calls")
    ledger.close(zero_axes=set(COST_AXES) - set(ledger.observed_axes))
    replay = replay_development_block_preparation(store, ledger.event_refs)
    nodes = tuple(
        _prepared_checkpoint_node(store, checkpoint_id, states[checkpoint_id], replay)
        for checkpoint_id in CheckpointId
    )
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256=preparation_policy_sha256,
        nodes=nodes,
        block_event_refs=replay.event_refs,
    )
    read_development_shared_checkpoint_manifest(store, manifest_ref)
    direct_state = states[direct_id]
    his_state = states[his_id]
    project_state = states[project_id]
    return PreparedBlockArtifacts(
        paired_block_ref=paired_block_ref,
        manifest_ref=manifest_ref,
        direct_initial_project=(
            direct_state[2] if direct_state[0] == "completed" else None
        ),
        system_his=his_state[2] if his_state[0] == "completed" else None,
        skeleton_initial_project=(
            project_state[2] if project_state[0] == "completed" else None
        ),
        trusted_skeleton=(
            project_state[3] if project_state[0] == "completed" else None
        ),
        event_refs=replay.event_refs,
    )


def _prepared_checkpoint_node(
    store: ArtifactStore,
    checkpoint_id: CheckpointId,
    state: tuple[str, str | None, Any, Any],
    replay: Any,
) -> CheckpointNode:
    status, reason, emission, trusted = state
    partition = tuple(
        reference
        for reference, event in zip(replay.event_refs, replay.events, strict=True)
        if event["checkpoint_id"] == checkpoint_id.value
    )
    artifact_ref = emission.artifact_ref if emission is not None else None
    return CheckpointNode(
        checkpoint_id=checkpoint_id,
        status=status,
        reason=reason,
        artifact_ref=artifact_ref,
        content_sha256=None if artifact_ref is None else artifact_ref.sha256,
        project_package_sha256=(
            emission.project_package_sha256
            if emission is not None
            and checkpoint_id is not CheckpointId.SHARED_SYSTEM_HIS
            else None
        ),
        trusted_skeleton_ref=(
            None if trusted is None else trusted.artifact_ref
        ),
        parent_checkpoint_ids=_PARENTS[checkpoint_id],
        consumer_methods=_CONSUMERS[checkpoint_id],
        source_event_refs=partition,
        source_events_sha256=_event_set_sha256(store, partition),
    )


def _preparation_failure_reason(exc: Exception) -> str:
    message = str(exc).strip()
    return f"{type(exc).__name__}:{message or 'no_message'}"


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


def blocked_methods_from_verified_manifest(
    store: ArtifactStore, reference: ArtifactRef
) -> dict[str, str]:
    """Map each blocked method to its verified failed shared prerequisite."""

    manifest = read_development_shared_checkpoint_manifest(store, reference)
    candidates: dict[str, list[Mapping[str, Any]]] = {}
    for node in manifest["nodes"]:
        if node["status"] == "completed":
            continue
        for method in node["consumer_methods"]:
            candidates.setdefault(method, []).append(node)
    blocked: dict[str, str] = {}
    for method, nodes in candidates.items():
        failed = [node for node in nodes if node["status"] == "failed"]
        origin = failed[0] if failed else nodes[0]
        blocked[method] = str(origin["checkpoint_id"])
    return blocked


def read_complete_development_shared_checkpoint_resume(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    paired_block_ref: ArtifactRef,
    preparation_policy_sha256: str,
) -> dict[str, Any]:
    """Accept only the exact, content-verified complete preparation for reuse."""

    expected_key = (
        f"shared-checkpoint-manifests/{paired_block_ref.sha256}/"
        f"{preparation_policy_sha256}"
    )
    try:
        _require_sha256(preparation_policy_sha256, "preparation policy")
        if reference.key != expected_key or store.reference(expected_key) != reference:
            raise ValueError("checkpoint manifest reference does not match requested resume")
        manifest = read_development_shared_checkpoint_manifest(store, reference)
        if manifest["paired_block_ref"] != paired_block_ref.to_dict():
            raise ValueError("checkpoint manifest paired block does not match requested resume")
        if manifest["preparation_policy_sha256"] != preparation_policy_sha256:
            raise ValueError("checkpoint manifest policy does not match requested resume")
        if manifest["manifest_status"] != "complete":
            raise ValueError("checkpoint manifest is incomplete")
    except (KeyError, OSError, TypeError, ValueError, RuntimeError) as exc:
        if isinstance(exc, SharedCheckpointResumeError):
            raise
        raise SharedCheckpointResumeError(
            f"shared checkpoint resume rejected ({exc}); use a new run ID"
        ) from exc
    return manifest


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
    system_his = nodes_by_id[CheckpointId.SHARED_SYSTEM_HIS]
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
    if system_his.status != "completed":
        if (
            skeleton.status != "not_run"
            or skeleton.reason != "dependency_failed:shared_system_his"
        ):
            raise ValueError(
                "skeleton checkpoint must be not_run after shared_system_his failure"
            )
    elif skeleton.status == "not_run":
        raise ValueError(
            "skeleton checkpoint cannot be not_run after completed shared_system_his"
        )


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
