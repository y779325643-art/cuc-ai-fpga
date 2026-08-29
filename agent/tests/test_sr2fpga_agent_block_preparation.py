from __future__ import annotations

import copy
import hashlib
import json

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


def _fixture(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    paired_block_ref = _write_paired_block(store)
    artifacts = MethodArtifactGateway(store)
    direct = artifacts.put_project("checkpoints/direct", _project("direct"))
    his = artifacts.put_planning(
        "checkpoints/his", PlanningArtifactKind.SYSTEM_HIS, {"intent": "counter"}
    )
    trusted = artifacts.put_project("checkpoints/trusted", _project("trusted"))
    skeleton = artifacts.put_project("checkpoints/skeleton", _project("skeleton"))
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
    assert {node["checkpoint_id"] for node in manifest["nodes"]} == {
        checkpoint.value for checkpoint in CheckpointId
    }


@pytest.mark.parametrize("mutation", ("content", "cross_block", "dag", "event_hash", "authority"))
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
    else:
        tampered["official_authority"] = True
    tampered_ref = store.put_blob(
        f"tampered/{mutation}",
        json.dumps(tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError):
        read_development_shared_checkpoint_manifest(store, tampered_ref)
