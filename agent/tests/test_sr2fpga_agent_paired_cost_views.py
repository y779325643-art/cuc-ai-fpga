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
from sr2fpga_agent.cost_accounting import (
    COST_AXES,
    AttemptCostLedger,
    reconcile_cost_events,
)
from sr2fpga_agent.full_pack_smoke import (
    FullPackMethodRecord,
    FullPackScenarioRecord,
    reconcile_excluded_full_pack,
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


def _write_paired_block(
    store: ArtifactStore, *, lineage_id: str = "primary"
) -> ArtifactRef:
    return write_development_paired_block(
        store,
        paired_block_id=f"pair-cost-{lineage_id}",
        semantic_instance_id=f"semantic-cost-{lineage_id}",
        replicate_id=f"replicate-{lineage_id}",
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
    unavailable_axis: str = "input_tokens",
):
    paired_block = json.loads(store.read_verified(paired_block_ref))
    prefix = f"paired/{paired_block_ref.sha256}"
    expected_policy = {
        "policy_version": "development-block-preparation-policy-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_id": paired_block["paired_block_id"],
        "paired_block_ref": paired_block_ref.to_dict(),
        "member_sample_ids": [f"sample-{index}" for index in range(6)],
        "physical_initial_model_call_ceiling": 3,
        "exclusive_model_call_ceilings": {
            "M0": 0,
            "M1": 0,
            "M2": 2,
            "M3": 1,
            "M4": 0,
            "M5": 0,
        },
        "expected_checkpoint_graph": [
            {
                "checkpoint_id": "direct_initial_project",
                "parent_checkpoint_ids": [],
                "consumer_methods": ["M0", "M1"],
                "planned_artifact_key": f"{prefix}/direct-initial-project",
            },
            {
                "checkpoint_id": "shared_system_his",
                "parent_checkpoint_ids": [],
                "consumer_methods": ["M3", "M4", "M5"],
                "planned_artifact_key": f"{prefix}/system-his",
            },
            {
                "checkpoint_id": "skeleton_initial_project",
                "parent_checkpoint_ids": ["shared_system_his"],
                "consumer_methods": ["M4", "M5"],
                "planned_artifact_key": f"{prefix}/skeleton-initial-project",
                "planned_trusted_skeleton_key": f"{prefix}/trusted-skeleton",
            },
        ],
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    expected_policy["preparation_policy_sha256"] = _canonical_sha256(
        expected_policy
    )
    gateway = MethodArtifactGateway(store)
    direct = gateway.put_project(
        f"{prefix}/direct-initial-project", _project("direct")
    )
    his = gateway.put_planning(
        f"{prefix}/system-his",
        PlanningArtifactKind.SYSTEM_HIS,
        {"intent": "counter"},
    )
    trusted = gateway.put_project(
        f"{prefix}/trusted-skeleton", _project("trusted")
    )
    skeleton = gateway.put_project(
        f"{prefix}/skeleton-initial-project",
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
            cost_delta = {"logical_model_calls": 1}
            unavailable_axes = None
            if unavailable:
                cost_delta[unavailable_axis] = None
                unavailable_axes = {
                    unavailable_axis: (
                        f"synthetic_axis_missing:{checkpoint}:{unavailable_axis}"
                    )
                }
            ledger.record_cost(
                stage={
                    "direct_initial_project": "block_direct_initial",
                    "shared_system_his": "block_req2his",
                    "skeleton_initial_project": "block_skeleton_initial",
                }[checkpoint],
                visibility_class="accounting",
                cost_delta=cost_delta,
                unavailable_axes=unavailable_axes,
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
                reason="dependency_failed:shared_system_his",
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
            reason = "dependency_failed:shared_system_his"
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
        preparation_policy_sha256=expected_policy["preparation_policy_sha256"],
        nodes=nodes,
        block_event_refs=ledger.event_refs,
    )
    return (
        manifest_ref,
        ledger.event_refs,
        {node.checkpoint_id.value: node for node in nodes},
        expected_policy,
    )


def _write_trajectory(
    store: ArtifactStore,
    *,
    method: str,
    logical_calls: int,
    wall_time: float,
    lineage_hashes: set[str],
    tamper_summary: bool = False,
    raw_lineage_mismatch: str | None = None,
    lineage_id: str = "primary",
):
    episode_id = f"episode-{lineage_id}-{method}"
    claimed_candidate_id = f"candidate-{lineage_id}-{method}"
    raw_candidate_id = (
        f"raw-candidate-{lineage_id}-{method}"
        if raw_lineage_mismatch == "candidate"
        else claimed_candidate_id
    )
    output_hash = hashlib.sha256(f"{lineage_id}:{method}".encode()).hexdigest()
    ledger = AttemptCostLedger(
        store,
        episode_id=episode_id,
        attempt_id="attempt-000",
        method_condition=method,
        failure_origin=None,
        candidate_id=raw_candidate_id,
        input_artifact_hashes=lineage_hashes,
    )
    ledger.record_cost(
        stage="method_exclusive",
        visibility_class="public",
        cost_delta={"logical_model_calls": logical_calls, "wall_time": wall_time},
        output_artifact_hashes=(output_hash,),
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
        f"synthetic-terminals/{lineage_id}/{method}",
        json.dumps({"lineage_id": lineage_id, "method": method}).encode(),
        media_type="application/json",
    )
    event_ids = [
        json.loads(store.read_verified(reference))["event_id"]
        for reference in ledger.event_refs
    ]
    claimed_input_hashes = set(lineage_hashes)
    if raw_lineage_mismatch == "input":
        claimed_input_hashes.add("e" * 64)
    claimed_output_hashes = {output_hash}
    if raw_lineage_mismatch == "output":
        claimed_output_hashes.add("f" * 64)
    without_id = {
        "contract_version": "trajectory-v2",
        "episode_id": episode_id,
        "method_condition": method,
        "failure_origin": None,
        "attempts": [
            {
                "attempt_id": "attempt-000",
                "candidate_id": claimed_candidate_id,
                "input_artifact_hashes": sorted(claimed_input_hashes),
                "output_artifact_hashes": sorted(claimed_output_hashes),
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
    nodes: dict[str, CheckpointNode],
    lineage_id: str = "primary",
) -> ArtifactRef:
    gateway = MethodArtifactGateway(store)
    direct = nodes["direct_initial_project"]
    his = nodes["shared_system_his"]
    skeleton = nodes["skeleton_initial_project"]
    m2 = gateway.put_project(
        f"synthetic-initial/{lineage_id}/M2",
        _project(f"{lineage_id}-M2"),
    )
    m3 = gateway.put_project(
        f"synthetic-initial/{lineage_id}/M3",
        _project(f"{lineage_id}-M3"),
    )
    candidate_by_method = {
        "M0": (direct.artifact_ref, direct.project_package_sha256),
        "M1": (direct.artifact_ref, direct.project_package_sha256),
        "M2": (m2.artifact_ref, m2.project_package_sha256),
        "M3": (m3.artifact_ref, m3.project_package_sha256),
        "M4": (skeleton.artifact_ref, skeleton.project_package_sha256),
        "M5": (skeleton.artifact_ref, skeleton.project_package_sha256),
    }
    smoke_methods = []
    for method in METHODS:
        candidate_ref, package_sha256 = candidate_by_method[method]
        smoke_methods.append(
            FullPackMethodRecord(
                method_condition=method,
                analysis_population="excluded",
                pack_sha256=hashlib.sha256(
                    f"{lineage_id}:{method}:pack".encode()
                ).hexdigest(),
                public_projection_sha256=paired_block[
                    "public_projection_sha256"
                ],
                candidate_artifact_key=candidate_ref.key,
                candidate_artifact_sha256=candidate_ref.sha256,
                project_package_sha256=package_sha256,
                skeleton_artifact_sha256=(
                    skeleton.trusted_skeleton_ref.sha256
                    if method in {"M4", "M5"}
                    else None
                ),
                planning_kind=(
                    "untyped_plan"
                    if method == "M2"
                    else "system_his"
                    if method in {"M3", "M4", "M5"}
                    else None
                ),
                planning_artifact_sha256=(
                    his.artifact_ref.sha256
                    if method in {"M3", "M4", "M5"}
                    else None
                ),
                h_status=(
                    "pass" if method in {"M3", "M4", "M5"} else "not_applicable"
                ),
                skeleton_mode=(
                    "none_free_full_project"
                    if method == "M3"
                    else "behavior_files"
                    if method in {"M4", "M5"}
                    else "none"
                ),
            )
        )
    projection = paired_block["public_projection_sha256"]
    scenario_inputs = (
        ("success", None, "passed", {"method_count": 6, "scope": "pre_candidate_emission_conformance"}),
        ("h_repair", "M5", "passed", {"his_corrections_used": 1, "rerun_complete_h_validation": True}),
        ("project_repair", "M1", "passed", {"repair_calls_attempted": 1, "repair_transitions": 1, "rerun_performed": True, "automatic_pass_credit": True}),
        ("non_ready", None, "needs_clarification", {"generation_calls": 0}),
        ("hidden_fail", "M0", "fail", {"opaque_outcome_only": True, "opaque_outcome_id": "synthetic-hidden-fail", "repair_after_hidden": False}),
        ("infrastructure_not_run", "M0", "not_run", {"reason": "synthetic_infrastructure", "opaque_outcome_id": "synthetic-infrastructure-not-run", "replacement_episode": False}),
    )
    _, source_ref = reconcile_excluded_full_pack(
        store,
        smoke_id=f"synthetic-cost-view-{lineage_id}",
        methods=smoke_methods,
        scenarios=(
            FullPackScenarioRecord(
                scenario_id=f"{lineage_id}-{kind}",
                scenario_kind=kind,
                analysis_population="excluded",
                public_projection_sha256=projection,
                method_condition=method,
                status=status,
                facts=facts,
            )
            for kind, method, status, facts in scenario_inputs
        ),
    )
    report = {
        "contract_version": "full-pack-runner-reconciliation-v2",
        "evaluation_scope": "excluded_development_conformance_only",
        "smoke_id": f"synthetic-cost-view-{lineage_id}",
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
        f"synthetic-full-pack/{lineage_id}/runner-v2",
        report,
        contract_key="full_pack_runner_reconciliation_v2",
    )


def _fixture(
    tmp_path,
    *,
    store: ArtifactStore | None = None,
    lineage_id: str = "primary",
    failed_checkpoint: str | None = None,
    unavailable_checkpoint: str | None = None,
    unavailable_axis: str = "input_tokens",
    tampered_summary_method: str | None = None,
    raw_lineage_mismatch: str | None = None,
):
    store = store or ArtifactStore(tmp_path / "store")
    paired_block_ref = _write_paired_block(store, lineage_id=lineage_id)
    paired_block = json.loads(store.read_verified(paired_block_ref))
    manifest_ref, block_event_refs, nodes, expected_policy = _write_checkpoint_sources(
        store,
        paired_block_ref=paired_block_ref,
        failed_checkpoint=failed_checkpoint,
        unavailable_checkpoint=unavailable_checkpoint,
        unavailable_axis=unavailable_axis,
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
            raw_lineage_mismatch=(
                raw_lineage_mismatch if method == "M0" else None
            ),
            lineage_id=lineage_id,
        )
        trajectories[method] = trajectory
        sources.append(MethodCostSource(method, "completed", trajectory[0]))
    full_pack_ref = (
        _write_full_pack(
            store,
            paired_block_ref=paired_block_ref,
            paired_block=paired_block,
            trajectories=trajectories,
            nodes=nodes,
            lineage_id=lineage_id,
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
        "expected_preparation_policy": expected_policy,
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
        expected_preparation_policy=fixture["expected_preparation_policy"],
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


def _assert_reconstruction_rejects_payload_tamper(
    fixture,
    payload: dict,
    *,
    label: str,
    monkeypatch,
) -> None:
    store = fixture["store"]
    tampered_ref = store.put_validated_json(
        f"tampered-reconciliations/{label}",
        payload,
        contract_key="development_paired_block_cost_reconciliation",
    )
    original_put = store.put_validated_json

    def preserve_tampered_ref(key, rebuilt, *, contract_key, registry=None):
        if contract_key == "development_paired_block_cost_reconciliation":
            return tampered_ref
        return original_put(
            key, rebuilt, contract_key=contract_key, registry=registry
        )

    monkeypatch.setattr(store, "put_validated_json", preserve_tampered_ref)
    with pytest.raises(
        PairedCostReconciliationError,
        match="does not match verified sources",
    ):
        read_development_paired_block_cost_reconciliation(
            store,
            tampered_ref,
            expected_preparation_policy=fixture["expected_preparation_policy"],
        )


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
        fixture["store"],
        reference,
        expected_preparation_policy=fixture["expected_preparation_policy"],
    ) == result


def test_initial_sp_proof_rejects_alternate_valid_m5_pre_repair_project(
    tmp_path,
) -> None:
    fixture = _fixture(tmp_path)
    result, _ = _reconcile(fixture)
    store = fixture["store"]
    runner = json.loads(store.read_verified(fixture["full_pack_ref"]))
    original_runner_methods = copy.deepcopy(runner["method_records"])
    smoke_ref = ArtifactRef(**runner["source_smoke_report_ref"])
    smoke = json.loads(store.read_verified(smoke_ref))
    alternate = MethodArtifactGateway(store).put_project(
        "tampered-initial/M5/alternate-valid-project",
        _project("alternate-valid-M5-initial"),
    )
    m5 = next(
        record for record in smoke["method_records"] if record["method_condition"] == "M5"
    )
    m5["candidate_artifact_key"] = alternate.artifact_ref.key
    m5["candidate_artifact_sha256"] = alternate.artifact_ref.sha256
    m5["project_package_sha256"] = alternate.project_package_sha256
    tampered_smoke_ref = store.put_validated_json(
        "tampered-full-pack-smokes/alternate-M5-initial",
        smoke,
        contract_key="full_pack_smoke_report",
    )
    runner["source_smoke_report_ref"] = tampered_smoke_ref.to_dict()
    assert runner["method_records"] == original_runner_methods
    tampered_runner_ref = store.put_validated_json(
        "tampered-full-pack-runners/alternate-M5-initial",
        runner,
        contract_key="full_pack_runner_reconciliation_v2",
    )
    fixture["full_pack_ref"] = tampered_runner_ref

    with pytest.raises(
        PairedCostReconciliationError,
        match="M5 initial candidate",
    ):
        _reconcile(fixture)

    tampered_cost = copy.deepcopy(result)
    tampered_cost["source_full_pack_runner_ref"] = tampered_runner_ref.to_dict()
    tampered_cost_ref = store.put_validated_json(
        "tampered-paired-costs/alternate-M5-initial",
        tampered_cost,
        contract_key="development_paired_block_cost_reconciliation",
    )
    with pytest.raises(
        PairedCostReconciliationError,
        match="M5 initial candidate",
    ):
        read_development_paired_block_cost_reconciliation(
            store,
            tampered_cost_ref,
            expected_preparation_policy=fixture["expected_preparation_policy"],
        )


def test_reducer_reconstructs_nonblocked_failed_method_with_trajectory(
    tmp_path,
) -> None:
    fixture = _fixture(tmp_path)
    fixture["methods"] = [
        replace(source, terminal_status="failed")
        if source.method_condition == "M2"
        else source
        for source in fixture["methods"]
    ]
    fixture["full_pack_ref"] = None

    result, reference = _reconcile(fixture)

    assert result["reconciliation_status"] == "incomplete"
    assert result["incomplete_reasons"] == ["method_terminal_status:M2:failed"]
    record = result["method_records"][2]
    assert record["terminal_status"] == "failed"
    assert record["trajectory_ref"] == fixture["trajectories"]["M2"][0].to_dict()
    assert record["cost_summary_refs"]
    assert record["attempt_event_refs"]
    assert record["exclusive_axes"]["logical_model_calls"]["value"] == 2
    assert record["standalone_attributed_axes"]["logical_model_calls"]["value"] == 2
    assert read_development_paired_block_cost_reconciliation(
        fixture["store"],
        reference,
        expected_preparation_policy=fixture["expected_preparation_policy"],
    ) == result


@pytest.mark.parametrize(
    "mutation",
    (
        "shared_redistributed",
        "shared_omitted",
        "m4_views_collapsed",
        "signed_delta",
    ),
)
def test_verified_reader_reconstructs_and_rejects_cost_algebra_tampering(
    tmp_path, monkeypatch, mutation: str
) -> None:
    fixture = _fixture(tmp_path)
    result, _reference = _reconcile(fixture)
    tampered = copy.deepcopy(result)
    records = {
        record["method_condition"]: record for record in tampered["method_records"]
    }
    contrasts = {
        contrast["contrast_id"]: contrast
        for contrast in tampered["incremental_contrasts"]
    }
    if mutation == "shared_redistributed":
        for method, value in zip(("M0", "M1"), (0, 2), strict=True):
            records[method]["standalone_attributed_axes"]["logical_model_calls"][
                "value"
            ] = value
    elif mutation == "shared_omitted":
        for method in ("M0", "M1"):
            records[method]["standalone_attributed_axes"]["logical_model_calls"][
                "value"
            ] = records[method]["exclusive_axes"]["logical_model_calls"]["value"]
    elif mutation == "m4_views_collapsed":
        after_his = contrasts["M4-M3"]["arms"][0]["axes"][
            "logical_model_calls"
        ]
        after_project = contrasts["M5-M4"]["arms"][1]["axes"][
            "logical_model_calls"
        ]
        assert after_his["value"] != after_project["value"]
        after_his["value"] = after_project["value"]
    else:
        signed = contrasts["M4-M3"]["signed_delta_axes"]["wall_time"]
        signed["value"] += 1

    _assert_reconstruction_rejects_payload_tamper(
        fixture,
        tampered,
        label=mutation,
        monkeypatch=monkeypatch,
    )


def test_verified_reader_rejects_direct_checkpoint_inserted_into_m1_incremental_arm(
    tmp_path, monkeypatch
) -> None:
    fixture = _fixture(tmp_path)
    result, _reference = _reconcile(fixture)
    replay = replay_development_block_preparation(
        fixture["store"], fixture["block_event_refs"]
    )
    m1_record = next(
        record
        for record in result["method_records"]
        if record["method_condition"] == "M1"
    )
    m1_m0 = next(
        contrast
        for contrast in result["incremental_contrasts"]
        if contrast["contrast_id"] == "M1-M0"
    )
    treatment = next(
        arm for arm in m1_m0["arms"] if arm["method_condition"] == "M1"
    )
    exclusive_calls = m1_record["exclusive_axes"]["logical_model_calls"]["value"]
    direct_calls = replay.checkpoint_axes["direct_initial_project"][
        "logical_model_calls"
    ]["value"]
    incremental_calls = treatment["axes"]["logical_model_calls"]["value"]

    assert exclusive_calls == 0
    assert direct_calls == 1
    assert incremental_calls == exclusive_calls == 0
    known_wrong_with_direct_checkpoint = exclusive_calls + direct_calls
    assert known_wrong_with_direct_checkpoint == 1

    tampered = copy.deepcopy(result)
    tampered_m1_m0 = next(
        contrast
        for contrast in tampered["incremental_contrasts"]
        if contrast["contrast_id"] == "M1-M0"
    )
    tampered_treatment = next(
        arm
        for arm in tampered_m1_m0["arms"]
        if arm["method_condition"] == "M1"
    )
    tampered_treatment["axes"]["logical_model_calls"]["value"] = (
        known_wrong_with_direct_checkpoint
    )

    _assert_reconstruction_rejects_payload_tamper(
        fixture,
        tampered,
        label="direct-checkpoint-in-m1-incremental",
        monkeypatch=monkeypatch,
    )


def test_verified_reader_rejects_duplicate_event_across_source_partitions(
    tmp_path,
) -> None:
    fixture = _fixture(tmp_path)
    result, _reference = _reconcile(fixture)
    tampered = copy.deepcopy(result)
    duplicate = tampered["source_event_partition"]["block_event_ids"][0]
    tampered["source_event_partition"]["method_event_ids"]["M0"].append(duplicate)
    tampered_ref = fixture["store"].put_blob(
        "tampered-reconciliations/partition-overlap",
        json.dumps(
            tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode(),
        media_type="application/json",
    )

    with pytest.raises(
        PairedCostReconciliationError,
        match="invalid paired-block cost reconciliation",
    ):
        read_development_paired_block_cost_reconciliation(
            fixture["store"],
            tampered_ref,
            expected_preparation_policy=fixture["expected_preparation_policy"],
        )


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
    assert forward["reconciliation"]["all_authority_fields_false"] is True
    assert all(
        forward[field] is False
        for field in (
            "official_outcome",
            "official_authority",
            "pass_credit_authority",
            "rq1_evidence",
            "rq2_evidence",
            "g3_accepted",
            "g4b_authorized",
        )
    )


@pytest.mark.parametrize(
    ("failed_checkpoint", "blocked", "affected_contrasts", "actual_calls"),
    (
        ("direct_initial_project", {"M0", "M1"}, {"M1-M0"}, 6),
        (
            "shared_system_his",
            {"M3", "M4", "M5"},
            {"M4-M3", "M5-M4"},
            4,
        ),
        (
            "skeleton_initial_project",
            {"M4", "M5"},
            {"M4-M3", "M5-M4"},
            6,
        ),
    ),
)
def test_reducer_preserves_pre_failure_cost_and_blocks_exact_consumers(
    tmp_path,
    failed_checkpoint: str,
    blocked: set[str],
    affected_contrasts: set[str],
    actual_calls: int,
) -> None:
    fixture = _fixture(tmp_path, failed_checkpoint=failed_checkpoint)
    result, _ = _reconcile(fixture)

    assert result["reconciliation_status"] == "incomplete"
    assert result["actual_block_axes"]["logical_model_calls"]["value"] == actual_calls
    records = {
        record["method_condition"]: record for record in result["method_records"]
    }
    assert {
        method
        for method, record in records.items()
        if record["terminal_status"] == "blocked_by_shared_checkpoint"
    } == blocked
    for method in METHODS:
        record = records[method]
        if method in blocked:
            assert record["blocked_checkpoint_id"] == failed_checkpoint
            assert failed_checkpoint in record["blocked_reason"]
            assert record["trajectory_ref"] is None
            assert record["cost_summary_refs"] == []
            assert record["attempt_event_refs"] == []
            assert all(
                axis == {"status": "measured", "value": 0, "reason": None}
                for axis in record["exclusive_axes"].values()
            )
            assert record["standalone_attributed_axes"]["logical_model_calls"][
                "value"
            ] >= 1
        else:
            assert record["terminal_status"] == "completed"
            assert record["trajectory_ref"] is not None
    contrasts = {
        contrast["contrast_id"]: contrast
        for contrast in result["incremental_contrasts"]
    }
    assert {
        contrast_id
        for contrast_id, contrast in contrasts.items()
        if contrast["status"] == "unavailable"
    } == affected_contrasts
    for contrast_id in affected_contrasts:
        assert failed_checkpoint in contrasts[contrast_id]["reason"]
        assert all(
            axis["status"] == "unavailable"
            for axis in contrasts[contrast_id]["signed_delta_axes"].values()
        )


def test_reducer_rejects_downstream_not_run_node_as_failure_origin(tmp_path) -> None:
    fixture = _fixture(tmp_path, failed_checkpoint="shared_system_his")
    methods = [
        (
            replace(source, blocked_checkpoint_id="skeleton_initial_project")
            if source.method_condition == "M4"
            else source
        )
        for source in fixture["methods"]
    ]

    with pytest.raises(PairedCostReconciliationError, match="verified failure origin"):
        _reconcile(fixture, methods=methods)


@pytest.mark.parametrize("unavailable_axis", COST_AXES)
def test_reducer_propagates_each_unavailable_axis_only_through_dependent_sums(
    tmp_path, unavailable_axis: str
) -> None:
    fixture = _fixture(
        tmp_path,
        unavailable_checkpoint="skeleton_initial_project",
        unavailable_axis=unavailable_axis,
    )
    result, _ = _reconcile(fixture)

    actual = result["actual_block_axes"][unavailable_axis]
    m4 = next(
        record
        for record in result["method_records"]
        if record["method_condition"] == "M4"
    )["standalone_attributed_axes"][unavailable_axis]
    m3 = next(
        record
        for record in result["method_records"]
        if record["method_condition"] == "M3"
    )["standalone_attributed_axes"][unavailable_axis]
    m4_m3 = result["incremental_contrasts"][1]

    assert actual["status"] == "unavailable"
    assert f"skeleton_initial_project:{unavailable_axis}" in actual["reason"]
    assert m4["status"] == "unavailable"
    assert f"skeleton_initial_project:{unavailable_axis}" in m4["reason"]
    assert m3["status"] == "measured"
    assert m3["value"] is not None
    assert m4_m3["arms"][0]["axes"][unavailable_axis]["status"] == (
        "unavailable"
    )
    assert m4_m3["arms"][1]["axes"][unavailable_axis]["status"] == "measured"
    signed = m4_m3["signed_delta_axes"][unavailable_axis]
    assert signed["status"] == "unavailable"
    assert signed["value"] is None
    assert unavailable_axis in signed["reason"]
    assert result["incremental_contrasts"][0]["signed_delta_axes"][
        unavailable_axis
    ]["status"] == "measured"


def test_verified_reader_reconstructs_partially_unavailable_contrast(tmp_path) -> None:
    fixture = _fixture(
        tmp_path,
        unavailable_checkpoint="skeleton_initial_project",
        unavailable_axis="input_tokens",
    )
    result, reference = _reconcile(fixture)

    contrast = result["incremental_contrasts"][1]
    assert contrast["status"] == "unavailable"
    assert any(
        axis["status"] == "unavailable"
        for arm in contrast["arms"]
        for axis in arm["axes"].values()
    )
    assert read_development_paired_block_cost_reconciliation(
        fixture["store"],
        reference,
        expected_preparation_policy=fixture["expected_preparation_policy"],
    ) == result


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


@pytest.mark.parametrize(
    ("lineage", "expected"),
        (
            ("trajectory", "M0 trajectory omits checkpoint lineage"),
            ("checkpoint", "checkpoint-manifest source is invalid"),
            ("full_pack", "full-pack source belongs to another paired block"),
        ),
)
def test_reducer_rejects_readable_same_store_cross_lineage_reference(
    tmp_path, lineage: str, expected: str
) -> None:
    fixture = _fixture(tmp_path, lineage_id="current")
    other = _fixture(
        tmp_path,
        store=fixture["store"],
        lineage_id="alternate",
    )
    alternate_trajectory_ref = other["trajectories"]["M0"][0]
    alternate_manifest_ref = other["manifest_ref"]
    alternate_full_pack_ref = other["full_pack_ref"]
    assert json.loads(
        fixture["store"].read_verified(alternate_trajectory_ref)
    )["method_condition"] == "M0"
    assert read_development_shared_checkpoint_manifest(
        fixture["store"], alternate_manifest_ref
    )["paired_block_ref"] == other["paired_block_ref"].to_dict()
    assert alternate_full_pack_ref is not None
    assert json.loads(
        fixture["store"].read_verified(alternate_full_pack_ref)
    )["paired_block_ref"] == other["paired_block_ref"].to_dict()

    if lineage == "trajectory":
        fixture["methods"] = [
            replace(
                fixture["methods"][0],
                trajectory_ref=alternate_trajectory_ref,
            ),
            *fixture["methods"][1:],
        ]
    elif lineage == "checkpoint":
        fixture["manifest_ref"] = alternate_manifest_ref
    else:
        fixture["full_pack_ref"] = alternate_full_pack_ref

    with pytest.raises(PairedCostReconciliationError, match=expected):
        _reconcile(fixture)


def test_reducer_reloads_raw_events_instead_of_trusting_summary_totals(tmp_path) -> None:
    fixture = _fixture(tmp_path, tampered_summary_method="M0")

    with pytest.raises(PairedCostReconciliationError):
        _reconcile(fixture)


@pytest.mark.parametrize(
    ("mismatch", "expected_message"),
    (
        ("candidate", "raw attempt candidate identity mismatch"),
        ("input", "raw input artifact hashes mismatch"),
        ("output", "raw output artifact hashes mismatch"),
    ),
)
def test_reducer_binds_raw_attempt_lineage_to_trajectory_claims(
    tmp_path, mismatch: str, expected_message: str
) -> None:
    fixture = _fixture(tmp_path, raw_lineage_mismatch=mismatch)

    with pytest.raises(PairedCostReconciliationError, match=expected_message):
        _reconcile(fixture)
