from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace

import pytest

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.block_cost_accounting import (
    BlockPreparationCostLedger,
    replay_development_block_preparation,
)
from sr2fpga_agent.block_preparation import (
    CheckpointId,
    CheckpointNode,
    read_development_shared_checkpoint_manifest,
    write_development_shared_checkpoint_manifest,
)
from sr2fpga_agent.cost_accounting import COST_AXES
from sr2fpga_agent.method_adapters import (
    MethodArtifactGateway,
    PlanningArtifactKind,
)
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.paired_block import (
    build_balanced_method_orders,
    write_development_paired_block,
)


def _project(tag: str) -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "checkpoint",
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {"ports": []},
        },
        "sources": [
            {"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {"toolchain_id": "open_source", "language_standard": "verilog-2005"},
    }
    return GeneratedProject(
        "checkpoint",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "rtl/top.v": f"// {tag}\nmodule top; endmodule\n",
        },
    )


def _write_paired_block(store: ArtifactStore) -> ArtifactRef:
    return write_development_paired_block(
        store,
        paired_block_id="pair-checkpoint-001",
        semantic_instance_id="semantic-checkpoint-001",
        replicate_id="replicate-000",
        public_projection_sha256="1" * 64,
        model_provenance_sha256="2" * 64,
        decoding_control_mode="documented_seed_control",
        requested_decoding_seed=17,
        execution_schedule_seed=991,
        method_order=build_balanced_method_orders(991)[0],
    )


def _event_hash(store: ArtifactStore, refs: tuple[ArtifactRef, ...]) -> str:
    ids = [json.loads(store.read_verified(reference))["event_id"] for reference in refs]
    return hashlib.sha256(
        json.dumps(ids, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _fixture(
    tmp_path,
    *,
    direct_key: str = "checkpoints/direct-initial-project",
    his_key: str = "checkpoints/system-his",
    skeleton_key: str = "checkpoints/skeleton-initial-project",
    reuse_direct_as_skeleton: bool = False,
):
    store = ArtifactStore(tmp_path / "store")
    paired_block_ref = _write_paired_block(store)
    artifacts = MethodArtifactGateway(store)
    direct = artifacts.put_project(direct_key, _project("direct"))
    his = artifacts.put_planning(
        his_key, PlanningArtifactKind.SYSTEM_HIS, {"intent": "counter"}
    )
    trusted = artifacts.put_project("checkpoints/trusted", _project("trusted"))
    skeleton = (
        direct
        if reuse_direct_as_skeleton
        else artifacts.put_project(skeleton_key, _project("skeleton"))
    )
    ledger = BlockPreparationCostLedger(store, paired_block_ref=paired_block_ref, failure_origin=None)
    for checkpoint, outputs in (
        ("direct_initial_project", (direct.artifact_ref,)),
        ("shared_system_his", (his.artifact_ref,)),
        ("skeleton_initial_project", (skeleton.artifact_ref, trusted.artifact_ref)),
    ):
        ledger.activate_checkpoint(checkpoint)
        ledger.record_checkpoint(
            checkpoint_id=checkpoint,
            event_kind="checkpoint_materialized",
            status="completed",
            output_refs=outputs,
        )
    ledger.close(zero_axes=COST_AXES)
    replay = replay_development_block_preparation(store, ledger.event_refs)
    partitions = {
        checkpoint: tuple(
            reference
            for reference, event in zip(replay.event_refs, replay.events, strict=True)
            if event["checkpoint_id"] == checkpoint
        )
        for checkpoint in CheckpointId
    }
    nodes = (
        CheckpointNode(
            CheckpointId.DIRECT_INITIAL_PROJECT,
            "completed",
            None,
            direct.artifact_ref,
            direct.artifact_ref.sha256,
            direct.project_package_sha256,
            None,
            (),
            ("M0", "M1"),
            partitions[CheckpointId.DIRECT_INITIAL_PROJECT],
            _event_hash(store, partitions[CheckpointId.DIRECT_INITIAL_PROJECT]),
        ),
        CheckpointNode(
            CheckpointId.SHARED_SYSTEM_HIS,
            "completed",
            None,
            his.artifact_ref,
            his.artifact_ref.sha256,
            None,
            None,
            (),
            ("M3", "M4", "M5"),
            partitions[CheckpointId.SHARED_SYSTEM_HIS],
            _event_hash(store, partitions[CheckpointId.SHARED_SYSTEM_HIS]),
        ),
        CheckpointNode(
            CheckpointId.SKELETON_INITIAL_PROJECT,
            "completed",
            None,
            skeleton.artifact_ref,
            skeleton.artifact_ref.sha256,
            skeleton.project_package_sha256,
            trusted.artifact_ref,
            (CheckpointId.SHARED_SYSTEM_HIS,),
            ("M4", "M5"),
            partitions[CheckpointId.SKELETON_INITIAL_PROJECT],
            _event_hash(store, partitions[CheckpointId.SKELETON_INITIAL_PROJECT]),
        ),
    )
    return store, paired_block_ref, nodes, ledger.event_refs


def _incomplete_direct_fixture(tmp_path, *, event_kind: str | None, reason: str = "raw_failure"):
    store = ArtifactStore(tmp_path / "store")
    paired_block_ref = _write_paired_block(store)
    artifacts = MethodArtifactGateway(store)
    his = artifacts.put_planning(
        "checkpoints/system-his", PlanningArtifactKind.SYSTEM_HIS, {"intent": "counter"}
    )
    trusted = artifacts.put_project("checkpoints/trusted", _project("trusted"))
    skeleton = artifacts.put_project(
        "checkpoints/skeleton-initial-project", _project("skeleton")
    )
    ledger = BlockPreparationCostLedger(store, paired_block_ref=paired_block_ref, failure_origin=None)
    ledger.activate_checkpoint("direct_initial_project")
    if event_kind is None:
        ledger.record_cost(
            stage="block_direct_initial",
            visibility_class="accounting",
            cost_delta={"logical_model_calls": 1},
        )
        direct_status = "failed"
    else:
        direct_status = "failed" if event_kind == "checkpoint_failed" else "not_run"
        ledger.record_checkpoint(
            checkpoint_id="direct_initial_project",
            event_kind=event_kind,
            status=direct_status,
            reason=reason,
        )
    for checkpoint, outputs in (
        ("shared_system_his", (his.artifact_ref,)),
        ("skeleton_initial_project", (skeleton.artifact_ref, trusted.artifact_ref)),
    ):
        ledger.activate_checkpoint(checkpoint)
        ledger.record_checkpoint(
            checkpoint_id=checkpoint,
            event_kind="checkpoint_materialized",
            status="completed",
            output_refs=outputs,
        )
    ledger.close(zero_axes=set(COST_AXES) - ledger.observed_axes)
    replay = replay_development_block_preparation(store, ledger.event_refs)
    partitions = {
        checkpoint: tuple(
            reference
            for reference, event in zip(replay.event_refs, replay.events, strict=True)
            if event["checkpoint_id"] == checkpoint
        )
        for checkpoint in CheckpointId
    }
    nodes = (
        CheckpointNode(
            CheckpointId.DIRECT_INITIAL_PROJECT,
            direct_status,
            reason,
            None,
            None,
            None,
            None,
            (),
            ("M0", "M1"),
            partitions[CheckpointId.DIRECT_INITIAL_PROJECT],
            _event_hash(store, partitions[CheckpointId.DIRECT_INITIAL_PROJECT]),
        ),
        CheckpointNode(
            CheckpointId.SHARED_SYSTEM_HIS,
            "completed",
            None,
            his.artifact_ref,
            his.artifact_ref.sha256,
            None,
            None,
            (),
            ("M3", "M4", "M5"),
            partitions[CheckpointId.SHARED_SYSTEM_HIS],
            _event_hash(store, partitions[CheckpointId.SHARED_SYSTEM_HIS]),
        ),
        CheckpointNode(
            CheckpointId.SKELETON_INITIAL_PROJECT,
            "completed",
            None,
            skeleton.artifact_ref,
            skeleton.artifact_ref.sha256,
            skeleton.project_package_sha256,
            trusted.artifact_ref,
            (CheckpointId.SHARED_SYSTEM_HIS,),
            ("M4", "M5"),
            partitions[CheckpointId.SKELETON_INITIAL_PROJECT],
            _event_hash(store, partitions[CheckpointId.SKELETON_INITIAL_PROJECT]),
        ),
    )
    return store, paired_block_ref, nodes, ledger.event_refs


def _unverified_manifest_ref(
    store: ArtifactStore,
    paired_block_ref: ArtifactRef,
    nodes: tuple[CheckpointNode, ...],
    event_refs: tuple[ArtifactRef, ...],
) -> ArtifactRef:
    payload = {
        "contract_version": "development-shared-checkpoint-manifest-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_ref": paired_block_ref.to_dict(),
        "preparation_policy_sha256": "3" * 64,
        "manifest_status": (
            "complete" if all(node.status == "completed" for node in nodes) else "incomplete"
        ),
        "nodes": [
            {
                "checkpoint_id": node.checkpoint_id.value,
                "status": node.status,
                "reason": node.reason,
                "artifact_ref": (
                    None if node.artifact_ref is None else node.artifact_ref.to_dict()
                ),
                "content_sha256": node.content_sha256,
                "project_package_sha256": node.project_package_sha256,
                "trusted_skeleton_ref": (
                    None
                    if node.trusted_skeleton_ref is None
                    else node.trusted_skeleton_ref.to_dict()
                ),
                "parent_checkpoint_ids": [
                    parent.value for parent in node.parent_checkpoint_ids
                ],
                "consumer_methods": list(node.consumer_methods),
                "source_event_refs": [
                    reference.to_dict() for reference in node.source_event_refs
                ],
                "source_events_sha256": node.source_events_sha256,
            }
            for node in nodes
        ],
        "block_event_refs": [reference.to_dict() for reference in event_refs],
        "block_events_sha256": _event_hash(store, event_refs),
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    return store.put_blob(
        "unverified-manifests/terminal-drift",
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(),
        media_type="application/json",
    )


def test_manifest_round_trip_replays_block_events_and_reconstructs_dag(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)

    reference = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    manifest = read_development_shared_checkpoint_manifest(store, reference)

    assert manifest["paired_block_ref"] == paired_block_ref.to_dict()
    assert manifest["manifest_status"] == "complete"
    assert manifest["rq1_evidence"] is False
    assert manifest["rq2_evidence"] is False
    assert {node["checkpoint_id"] for node in manifest["nodes"]} == {
        checkpoint.value for checkpoint in CheckpointId
    }


@pytest.mark.parametrize(
    "mutation",
    ("content", "cross_block", "dag", "event_hash", "authority", "rq1", "rq2"),
)
def test_verified_manifest_reader_rejects_tampering(tmp_path, mutation: str) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)
    reference = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    payload = json.loads(store.read_verified(reference))
    tampered = copy.deepcopy(payload)
    if mutation == "content":
        tampered["nodes"][0]["content_sha256"] = "f" * 64
    elif mutation == "cross_block":
        tampered["paired_block_ref"] = {**paired_block_ref.to_dict(), "key": "paired-blocks/other"}
    elif mutation == "dag":
        tampered["nodes"][2]["parent_checkpoint_ids"] = []
    elif mutation == "event_hash":
        tampered["nodes"][1]["source_events_sha256"] = "f" * 64
    elif mutation == "authority":
        tampered["official_authority"] = True
    elif mutation == "rq1":
        tampered["rq1_evidence"] = True
    else:
        tampered["rq2_evidence"] = True
    tampered_ref = store.put_blob(
        f"tampered/{mutation}",
        json.dumps(tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError):
        read_development_shared_checkpoint_manifest(store, tampered_ref)


@pytest.mark.parametrize(
    ("event_kind", "node_status"),
    (("checkpoint_failed", "not_run"), ("checkpoint_not_run", "failed")),
)
def test_writer_rejects_incomplete_node_status_drift(tmp_path, event_kind, node_status) -> None:
    store, paired_block_ref, nodes, event_refs = _incomplete_direct_fixture(
        tmp_path, event_kind=event_kind
    )
    nodes = (replace(nodes[0], status=node_status), *nodes[1:])

    with pytest.raises(ValueError, match="terminal event"):
        write_development_shared_checkpoint_manifest(
            store,
            paired_block_ref=paired_block_ref,
            preparation_policy_sha256="3" * 64,
            nodes=nodes,
            block_event_refs=event_refs,
        )


def test_writer_rejects_incomplete_node_reason_drift(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _incomplete_direct_fixture(
        tmp_path, event_kind="checkpoint_failed"
    )
    nodes = (replace(nodes[0], reason="reason_drift"), *nodes[1:])

    with pytest.raises(ValueError, match="terminal event"):
        write_development_shared_checkpoint_manifest(
            store,
            paired_block_ref=paired_block_ref,
            preparation_policy_sha256="3" * 64,
            nodes=nodes,
            block_event_refs=event_refs,
        )


def test_reader_rejects_incomplete_node_terminal_status_drift(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _incomplete_direct_fixture(
        tmp_path, event_kind="checkpoint_failed"
    )
    drifted_nodes = (replace(nodes[0], status="not_run"), *nodes[1:])
    reference = _unverified_manifest_ref(
        store, paired_block_ref, drifted_nodes, event_refs
    )

    with pytest.raises(ValueError, match="terminal event"):
        read_development_shared_checkpoint_manifest(store, reference)


def test_writer_rejects_incomplete_node_without_terminal_event(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _incomplete_direct_fixture(
        tmp_path, event_kind=None
    )

    with pytest.raises(ValueError, match="terminal event"):
        write_development_shared_checkpoint_manifest(
            store,
            paired_block_ref=paired_block_ref,
            preparation_policy_sha256="3" * 64,
            nodes=nodes,
            block_event_refs=event_refs,
        )


def test_writer_rejects_incomplete_node_with_duplicate_terminal_events(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _incomplete_direct_fixture(
        tmp_path, event_kind="checkpoint_failed"
    )
    ledger = BlockPreparationCostLedger(store, paired_block_ref=paired_block_ref, failure_origin=None)
    # Build a replay-valid duplicate-terminal stream instead of mutating a signed event.
    ledger.activate_checkpoint("direct_initial_project")
    ledger.record_checkpoint(
        checkpoint_id="direct_initial_project",
        event_kind="checkpoint_failed",
        status="failed",
        reason="raw_failure",
    )
    ledger.record_checkpoint(
        checkpoint_id="direct_initial_project",
        event_kind="checkpoint_failed",
        status="failed",
        reason="raw_failure",
    )
    ledger.activate_checkpoint("shared_system_his")
    ledger.record_checkpoint(
        checkpoint_id="shared_system_his",
        event_kind="checkpoint_materialized",
        status="completed",
        output_refs=(nodes[1].artifact_ref,),
    )
    ledger.activate_checkpoint("skeleton_initial_project")
    ledger.record_checkpoint(
        checkpoint_id="skeleton_initial_project",
        event_kind="checkpoint_materialized",
        status="completed",
        output_refs=(nodes[2].artifact_ref, nodes[2].trusted_skeleton_ref),
    )
    ledger.close(zero_axes=COST_AXES)
    replay = replay_development_block_preparation(store, ledger.event_refs)
    duplicate_nodes = tuple(
        replace(
            node,
            source_event_refs=tuple(
                reference
                for reference, event in zip(replay.event_refs, replay.events, strict=True)
                if event["checkpoint_id"] == node.checkpoint_id.value
            ),
        )
        for node in nodes
    )
    duplicate_nodes = tuple(
        replace(node, source_events_sha256=_event_hash(store, node.source_event_refs))
        for node in duplicate_nodes
    )

    with pytest.raises(ValueError, match="terminal event"):
        write_development_shared_checkpoint_manifest(
            store,
            paired_block_ref=paired_block_ref,
            preparation_policy_sha256="3" * 64,
            nodes=duplicate_nodes,
            block_event_refs=ledger.event_refs,
        )


@pytest.mark.parametrize(
    "kwargs",
    (
        {"direct_key": "checkpoints/wrong"},
        {"his_key": "checkpoints/wrong"},
        {"skeleton_key": "checkpoints/wrong"},
        {"reuse_direct_as_skeleton": True},
    ),
)
def test_writer_rejects_wrong_or_reused_checkpoint_artifact_keys(tmp_path, kwargs) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path, **kwargs)

    with pytest.raises(
        ValueError,
        match="checkpoint artifact key|checkpoint artifacts must be distinct",
    ):
        write_development_shared_checkpoint_manifest(
            store,
            paired_block_ref=paired_block_ref,
            preparation_policy_sha256="3" * 64,
            nodes=nodes,
            block_event_refs=event_refs,
        )


def test_writer_rejects_schema_valid_trusted_skeleton_ref_reuse(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)
    reused_nodes = (
        *nodes[:2],
        replace(nodes[2], trusted_skeleton_ref=nodes[2].artifact_ref),
    )

    with pytest.raises(ValueError, match="trusted skeleton cannot substitute"):
        write_development_shared_checkpoint_manifest(
            store,
            paired_block_ref=paired_block_ref,
            preparation_policy_sha256="3" * 64,
            nodes=reused_nodes,
            block_event_refs=event_refs,
        )
