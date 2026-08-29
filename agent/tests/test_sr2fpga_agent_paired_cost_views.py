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
    write_development_shared_checkpoint_manifest,
)
from sr2fpga_agent.cost_accounting import (
    COST_AXES,
    AttemptCostLedger,
    reconcile_cost_events,
)
from sr2fpga_agent.method_adapters import MethodArtifactGateway, PlanningArtifactKind
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.paired_block import (
    build_balanced_method_orders,
    write_development_paired_block,
)
from sr2fpga_agent.paired_cost_views import (
    MethodCostSource,
    PairedCostReconciliationError,
    read_development_paired_block_cost_reconciliation,
    reconcile_development_paired_block_costs,
)


METHODS = ("M0", "M1", "M2", "M3", "M4", "M5")
PREREQUISITES = {
    "M0": ("direct_initial_project",),
    "M1": ("direct_initial_project",),
    "M2": (),
    "M3": ("shared_system_his",),
    "M4": ("shared_system_his", "skeleton_initial_project"),
    "M5": ("shared_system_his", "skeleton_initial_project"),
}


def _canonical_sha256(payload) -> str:
    content = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


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
        paired_block_id="pair-cost-001",
        semantic_instance_id="semantic-cost-001",
        replicate_id="replicate-000",
        public_projection_sha256="1" * 64,
        model_provenance_sha256="2" * 64,
        decoding_control_mode="documented_seed_control",
        requested_decoding_seed=17,
        execution_schedule_seed=991,
        method_order=build_balanced_method_orders(991)[0],
    )


def _write_checkpoint_sources(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    failed_checkpoint: str | None = None,
    unavailable_checkpoint: str | None = None,
):
    gateway = MethodArtifactGateway(store)
    direct = gateway.put_project(
        f"paired/{paired_block_ref.sha256}/direct-initial-project", _project("direct")
    )
    his = gateway.put_planning(
        f"paired/{paired_block_ref.sha256}/system-his",
        PlanningArtifactKind.SYSTEM_HIS,
        {"intent": "counter"},
    )
    trusted = gateway.put_project(
        f"paired/{paired_block_ref.sha256}/trusted-skeleton", _project("trusted")
    )
    skeleton = gateway.put_project(
        f"paired/{paired_block_ref.sha256}/skeleton-initial-project",
        _project("skeleton"),
    )
    artifacts = {
        "direct_initial_project": (direct.artifact_ref,),
        "shared_system_his": (his.artifact_ref,),
        "skeleton_initial_project": (skeleton.artifact_ref, trusted.artifact_ref),
    }
    ledger = BlockPreparationCostLedger(
        store, paired_block_ref=paired_block_ref, failure_origin=None
    )
    blocked_downstream = False
    for checkpoint in (
        "direct_initial_project",
        "shared_system_his",
        "skeleton_initial_project",
    ):
        ledger.activate_checkpoint(checkpoint)
        is_not_run = blocked_downstream
        if not is_not_run:
            unavailable = checkpoint == unavailable_checkpoint
            ledger.record_cost(
                stage={
                    "direct_initial_project": "block_direct_initial",
                    "shared_system_his": "block_req2his",
                    "skeleton_initial_project": "block_skeleton_initial",
                }[checkpoint],
                visibility_class="accounting",
                cost_delta={
                    "logical_model_calls": 1,
                    **({"input_tokens": None} if unavailable else {}),
                },
                unavailable_axes=(
                    {"input_tokens": "synthetic_token_usage_missing"}
                    if unavailable
                    else None
                ),
            )
        if checkpoint == failed_checkpoint:
            ledger.record_checkpoint(
                checkpoint_id=checkpoint,
                event_kind="checkpoint_failed",
                status="failed",
                reason="synthetic_checkpoint_failure",
            )
            blocked_downstream = checkpoint == "shared_system_his"
        elif is_not_run:
            ledger.record_checkpoint(
                checkpoint_id=checkpoint,
                event_kind="checkpoint_not_run",
                status="not_run",
                reason="blocked_by_shared_checkpoint",
            )
        else:
            ledger.record_checkpoint(
                checkpoint_id=checkpoint,
                event_kind="checkpoint_materialized",
                status="completed",
                output_refs=artifacts[checkpoint],
            )
    ledger.close(zero_axes=set(COST_AXES) - ledger.observed_axes)
    replay = replay_development_block_preparation(store, ledger.event_refs)
    partitions = {
        checkpoint.value: tuple(
            reference
            for reference, event in zip(replay.event_refs, replay.events, strict=True)
            if event["checkpoint_id"] == checkpoint.value
        )
        for checkpoint in CheckpointId
    }
    nodes = []
    for checkpoint in CheckpointId:
        checkpoint_id = checkpoint.value
        event_refs = partitions[checkpoint_id]
        event_ids = [
            json.loads(store.read_verified(reference))["event_id"]
            for reference in event_refs
        ]
        status = "completed"
        reason = None
        if checkpoint_id == failed_checkpoint:
            status = "failed"
            reason = "synthetic_checkpoint_failure"
        elif failed_checkpoint == "shared_system_his" and checkpoint_id == "skeleton_initial_project":
            status = "not_run"
            reason = "blocked_by_shared_checkpoint"
        artifact_ref = artifacts[checkpoint_id][0] if status == "completed" else None
        nodes.append(
            CheckpointNode(
                checkpoint,
                status,
                reason,
                artifact_ref,
                artifact_ref.sha256 if artifact_ref is not None else None,
                (
                    direct.project_package_sha256
                    if checkpoint is CheckpointId.DIRECT_INITIAL_PROJECT and status == "completed"
                    else skeleton.project_package_sha256
                    if checkpoint is CheckpointId.SKELETON_INITIAL_PROJECT and status == "completed"
                    else None
                ),
                (
                    trusted.artifact_ref
                    if checkpoint is CheckpointId.SKELETON_INITIAL_PROJECT and status == "completed"
                    else None
                ),
                (
                    (CheckpointId.SHARED_SYSTEM_HIS,)
                    if checkpoint is CheckpointId.SKELETON_INITIAL_PROJECT
                    else ()
                ),
                {
                    CheckpointId.DIRECT_INITIAL_PROJECT: ("M0", "M1"),
                    CheckpointId.SHARED_SYSTEM_HIS: ("M3", "M4", "M5"),
                    CheckpointId.SKELETON_INITIAL_PROJECT: ("M4", "M5"),
                }[checkpoint],
                event_refs,
                _canonical_sha256(event_ids),
            )
        )
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=ledger.event_refs,
    )
    return manifest_ref, ledger.event_refs, {node.checkpoint_id.value: node for node in nodes}


def _write_trajectory(
    store: ArtifactStore,
    *,
    method: str,
    logical_calls: int,
    wall_time: float,
    lineage_hashes: set[str],
    tamper_summary: bool = False,
):
    episode_id = f"episode-{method}"
    ledger = AttemptCostLedger(
        store,
        episode_id=episode_id,
        attempt_id="attempt-000",
        method_condition=method,
        failure_origin=None,
        candidate_id=f"candidate-{method}",
        input_artifact_hashes=lineage_hashes,
    )
    ledger.record_cost(
        stage="method_exclusive",
        visibility_class="public",
        cost_delta={"logical_model_calls": logical_calls, "wall_time": wall_time},
        output_artifact_hashes=(hashlib.sha256(method.encode()).hexdigest(),),
    )
    ledger.close(zero_axes=set(COST_AXES) - ledger.observed_axes)
    if tamper_summary:
        staging = reconcile_cost_events(
            store,
            ledger.event_refs,
            summary_key=f"staging-cost-summaries/{episode_id}/attempt-000",
        )
        declared_summary = copy.deepcopy(staging.payload)
        declared_summary["axes"]["logical_model_calls"]["value"] += 1
        summary_ref = store.put_validated_json(
            f"cost-summaries/{episode_id}/attempt-000",
            declared_summary,
            contract_key="cost_summary",
        )
    else:
        summary_ref = reconcile_cost_events(store, ledger.event_refs).artifact_ref
    terminal_ref = store.put_blob(
        f"synthetic-terminals/{method}",
        json.dumps({"method": method}).encode(),
        media_type="application/json",
    )
    event_ids = [
        json.loads(store.read_verified(reference))["event_id"]
        for reference in ledger.event_refs
    ]
    without_id = {
        "contract_version": "trajectory-v2",
        "episode_id": episode_id,
        "method_condition": method,
        "failure_origin": None,
        "attempts": [
            {
                "attempt_id": "attempt-000",
                "candidate_id": f"candidate-{method}",
                "input_artifact_hashes": sorted(lineage_hashes),
                "output_artifact_hashes": [hashlib.sha256(method.encode()).hexdigest()],
                "attempt_event_refs": [reference.to_dict() for reference in ledger.event_refs],
                "cost_summary_ref": summary_ref.to_dict(),
                "source_events_sha256": _canonical_sha256(event_ids),
                "accounting_closed": True,
            }
        ],
        "terminal_candidate_ref": terminal_ref.to_dict(),
        "development_hidden_outcome_ref": None,
        "lineage_complete": True,
        "missing_lineage_reasons": [],
    }
    trajectory = {
        **without_id,
        "trajectory_id": "trajectory-v2-" + _canonical_sha256(without_id),
    }
    trajectory_ref = store.put_validated_json(
        f"trajectories/{episode_id}/{method}",
        trajectory,
        contract_key="trajectory_v2",
    )
    return trajectory_ref, trajectory, summary_ref, ledger.event_refs, terminal_ref


def _write_full_pack(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    paired_block: dict,
    trajectories: dict[str, tuple],
) -> ArtifactRef:
    source_ref = store.put_blob(
        "synthetic-full-pack/source",
        b'{"synthetic":true}\n',
        media_type="application/json",
    )
    report = {
        "contract_version": "full-pack-runner-reconciliation-v2",
        "evaluation_scope": "excluded_development_conformance_only",
        "smoke_id": "synthetic-cost-view",
        "analysis_population": "excluded",
        "g3_accepted": False,
        "g4b_authorized": False,
        "official_outcome": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "public_projection_sha256": paired_block["public_projection_sha256"],
        "source_smoke_report_ref": source_ref.to_dict(),
        "paired_block_ref": paired_block_ref.to_dict(),
        "method_order": paired_block["method_order"],
        "actual_method_order": paired_block["method_order"],
        "method_order_verified": True,
        "method_records": [
            {
                "method_condition": method,
                "episode_id": trajectories[method][1]["episode_id"],
                "trajectory_ref": trajectories[method][0].to_dict(),
                "terminal_candidate_ref": trajectories[method][4].to_dict(),
                "cost_summary_refs": [trajectories[method][2].to_dict()],
                "development_hidden_outcome_ref": None,
                "lineage_complete": True,
                "all_cost_axes_classified": True,
            }
            for method in METHODS
        ],
        "reconciliation": {
            "method_set": list(METHODS),
            "same_public_projection": True,
            "all_trajectories_verified": True,
            "all_cost_axes_classified": True,
            "matching_terminal_seals": True,
            "opaque_hidden_ref_count": 0,
            "blocking_gaps": [
                "runtime_scenario_evidence_reconciliation",
                "official_public_terminal_hidden_authority",
                "g4b_campaign_authority",
            ],
        },
    }
    return store.put_validated_json(
        "synthetic-full-pack/runner-v2",
        report,
        contract_key="full_pack_runner_reconciliation_v2",
    )


def _fixture(
    tmp_path,
    *,
    failed_checkpoint: str | None = None,
    unavailable_checkpoint: str | None = None,
    tampered_summary_method: str | None = None,
):
    store = ArtifactStore(tmp_path / "store")
    paired_block_ref = _write_paired_block(store)
    paired_block = json.loads(store.read_verified(paired_block_ref))
    manifest_ref, block_event_refs, nodes = _write_checkpoint_sources(
        store,
        paired_block_ref=paired_block_ref,
        failed_checkpoint=failed_checkpoint,
        unavailable_checkpoint=unavailable_checkpoint,
    )
    base_hashes = {
        paired_block_ref.sha256,
        manifest_ref.sha256,
        *(reference.sha256 for reference in block_event_refs),
    }
    blocked = {
        "direct_initial_project": {"M0", "M1"},
        "shared_system_his": {"M3", "M4", "M5"},
        "skeleton_initial_project": {"M4", "M5"},
    }.get(failed_checkpoint, set())
    exclusive_calls = {"M0": 0, "M1": 0, "M2": 2, "M3": 1, "M4": 0, "M5": 0}
    wall_times = {"M0": 0.0, "M1": 0.0, "M2": 2.0, "M3": 1.0, "M4": 0.5, "M5": 0.0}
    trajectories = {}
    sources = []
    for method in METHODS:
        if method in blocked:
            sources.append(
                MethodCostSource(
                    method,
                    "blocked_by_shared_checkpoint",
                    None,
                    failed_checkpoint,
                )
            )
            continue
        hashes = set(base_hashes)
        hashes.update(
            nodes[checkpoint].artifact_ref.sha256
            for checkpoint in PREREQUISITES[method]
            if nodes[checkpoint].artifact_ref is not None
        )
        trajectory = _write_trajectory(
            store,
            method=method,
            logical_calls=exclusive_calls[method],
            wall_time=wall_times[method],
            lineage_hashes=hashes,
            tamper_summary=method == tampered_summary_method,
        )
        trajectories[method] = trajectory
        sources.append(MethodCostSource(method, "completed", trajectory[0]))
    full_pack_ref = (
        _write_full_pack(
            store,
            paired_block_ref=paired_block_ref,
            paired_block=paired_block,
            trajectories=trajectories,
        )
        if failed_checkpoint is None
        else None
    )
    return {
        "store": store,
        "paired_block_ref": paired_block_ref,
        "manifest_ref": manifest_ref,
        "block_event_refs": block_event_refs,
        "methods": sources,
        "full_pack_ref": full_pack_ref,
        "trajectories": trajectories,
    }


def _reconcile(fixture, *, methods=None):
    return reconcile_development_paired_block_costs(
        fixture["store"],
        paired_block_ref=fixture["paired_block_ref"],
        checkpoint_manifest_ref=fixture["manifest_ref"],
        block_event_refs=fixture["block_event_refs"],
        methods=fixture["methods"] if methods is None else methods,
        source_full_pack_runner_ref=fixture["full_pack_ref"],
        reducer_policy_sha256="4" * 64,
    )


def _standalone(result: dict, method: str, axis: str):
    record = next(
        item for item in result["method_records"] if item["method_condition"] == method
    )
    return record["standalone_attributed_axes"][axis]["value"]


def _contrast_arm(result: dict, contrast: str, method: str, axis: str):
    record = next(
        item for item in result["incremental_contrasts"] if item["contrast_id"] == contrast
    )
    arm = next(item for item in record["arms"] if item["method_condition"] == method)
    return arm["axes"][axis]["value"]


def test_reducer_reconciles_actual_standalone_and_incremental_call_algebra(tmp_path) -> None:
    fixture = _fixture(tmp_path)
    result, reference = _reconcile(fixture)

    assert result["actual_block_axes"]["logical_model_calls"]["value"] == 6
    assert _standalone(result, "M0", "logical_model_calls") == 1
    assert _standalone(result, "M1", "logical_model_calls") == 1
    assert _standalone(result, "M2", "logical_model_calls") == 2
    assert _standalone(result, "M3", "logical_model_calls") == 2
    assert _standalone(result, "M4", "logical_model_calls") == 2
    assert _standalone(result, "M5", "logical_model_calls") == 2
    assert _contrast_arm(result, "M4-M3", "M4", "logical_model_calls") == 1
    assert _contrast_arm(result, "M4-M3", "M3", "logical_model_calls") == 1
    assert result["incremental_contrasts"][1]["signed_delta_axes"]["wall_time"] == {
        "status": "measured",
        "value": -0.5,
        "reason": None,
    }
    assert read_development_paired_block_cost_reconciliation(
        fixture["store"], reference
    ) == result


def test_reducer_is_order_invariant_and_records_an_exact_disjoint_partition(tmp_path) -> None:
    fixture = _fixture(tmp_path)
    forward, _ = _reconcile(fixture)
    reverse, _ = _reconcile(fixture, methods=reversed(fixture["methods"]))

    assert forward == reverse
    partition = forward["source_event_partition"]
    event_ids = list(partition["block_event_ids"])
    for method in METHODS:
        event_ids.extend(partition["method_event_ids"][method])
    assert len(event_ids) == len(set(event_ids))
    assert partition["source_events_sha256"] == _canonical_sha256(
        {
            "block_event_ids": partition["block_event_ids"],
            "method_event_ids": partition["method_event_ids"],
        }
    )


def test_reducer_preserves_pre_failure_cost_and_marks_affected_contrast_unavailable(
    tmp_path,
) -> None:
    fixture = _fixture(tmp_path, failed_checkpoint="direct_initial_project")
    result, _ = _reconcile(fixture)

    assert result["reconciliation_status"] == "incomplete"
    assert result["actual_block_axes"]["logical_model_calls"]["value"] == 6
    assert _standalone(result, "M0", "logical_model_calls") == 1
    assert _standalone(result, "M1", "logical_model_calls") == 1
    contrast = result["incremental_contrasts"][0]
    assert contrast["status"] == "unavailable"
    assert "direct_initial_project" in contrast["reason"]
    assert all(
        axis["status"] == "unavailable"
        for axis in contrast["signed_delta_axes"].values()
    )


def test_reducer_propagates_unavailable_axes_only_through_dependent_sums(tmp_path) -> None:
    fixture = _fixture(tmp_path, unavailable_checkpoint="skeleton_initial_project")
    result, _ = _reconcile(fixture)

    assert result["actual_block_axes"]["input_tokens"]["status"] == "unavailable"
    assert next(
        record
        for record in result["method_records"]
        if record["method_condition"] == "M4"
    )["standalone_attributed_axes"]["input_tokens"]["status"] == "unavailable"
    assert next(
        record
        for record in result["method_records"]
        if record["method_condition"] == "M3"
    )["standalone_attributed_axes"]["input_tokens"] == {
        "status": "measured",
        "value": 0,
        "reason": None,
    }
    m4_m3 = result["incremental_contrasts"][1]
    assert m4_m3["arms"][0]["axes"]["input_tokens"]["status"] == "unavailable"
    assert m4_m3["arms"][1]["axes"]["input_tokens"]["status"] == "measured"
    assert m4_m3["signed_delta_axes"]["input_tokens"]["status"] == "unavailable"


def test_reducer_rejects_missing_checkpoint_lineage_and_duplicate_method_partitions(
    tmp_path,
) -> None:
    fixture = _fixture(tmp_path)
    m0 = fixture["methods"][0]
    missing_lineage = replace(m0, trajectory_ref=fixture["trajectories"]["M2"][0])
    duplicate_partition = [
        m0,
        replace(fixture["methods"][1], trajectory_ref=m0.trajectory_ref),
        *fixture["methods"][2:],
    ]

    for methods in (
        [missing_lineage, *fixture["methods"][1:]],
        duplicate_partition,
    ):
        with pytest.raises(PairedCostReconciliationError):
            _reconcile(fixture, methods=methods)


def test_reducer_rejects_full_pack_cross_lineage(tmp_path) -> None:
    fixture = _fixture(tmp_path)
    other = _fixture(tmp_path / "other")
    fixture["full_pack_ref"] = other["full_pack_ref"]

    with pytest.raises(PairedCostReconciliationError):
        _reconcile(fixture)


def test_reducer_reloads_raw_events_instead_of_trusting_summary_totals(tmp_path) -> None:
    fixture = _fixture(tmp_path, tampered_summary_method="M0")

    with pytest.raises(PairedCostReconciliationError):
        _reconcile(fixture)
