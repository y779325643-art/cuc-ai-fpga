from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace

import pytest

from sr2fpga_agent.artifact_store import (
    ArtifactIntegrityError,
    ArtifactRef,
    ArtifactStore,
)
from sr2fpga_agent.block_cost_accounting import (
    BlockPreparationCostLedger,
    replay_development_block_preparation,
)
from sr2fpga_agent.block_preparation import (
    BlockPreparationFacades,
    CheckpointId,
    CheckpointNode,
    SharedCheckpointResumeError,
    blocked_methods_from_verified_manifest,
    prepare_development_paired_block,
    read_complete_development_shared_checkpoint_resume,
    read_development_shared_checkpoint_manifest,
    verify_development_shared_checkpoint_manifest_against_policy,
    write_development_shared_checkpoint_manifest,
)
from sr2fpga_agent.cost_accounting import COST_AXES
from sr2fpga_agent.frozen_context import freeze_ready_requirement_context
from sr2fpga_agent.method_adapters import (
    MethodArtifactGateway,
    PairingKey,
    PlanningArtifactKind,
)
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.paired_block import (
    build_balanced_method_orders,
    write_development_paired_block,
)
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary


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


def _platform() -> PlatformProfile:
    return PlatformProfile("generic_verilog", "generic", "open_source")


def _context():
    request = ProjectRequest(
        "counter",
        8,
        "counter8",
        "Build an 8-bit synchronous counter with active-low reset.",
    )
    return freeze_ready_requirement_context(
        evaluate_requirement_boundary(request, _platform()), _platform()
    )


def _write_paired_block(store: ArtifactStore, *, public_projection_sha256="1" * 64) -> ArtifactRef:
    return write_development_paired_block(
        store,
        paired_block_id="pair-checkpoint-001",
        semantic_instance_id="semantic-checkpoint-001",
        replicate_id="replicate-000",
        public_projection_sha256=public_projection_sha256,
        model_provenance_sha256="2" * 64,
        decoding_control_mode="documented_seed_control",
        requested_decoding_seed=17,
        execution_schedule_seed=991,
        method_order=build_balanced_method_orders(991)[0],
    )


class _CountingClient:
    def __init__(
        self,
        events: list[str],
        event: str,
        *,
        failure: Exception | None = None,
    ) -> None:
        self.calls = 0
        self._events = events
        self._event = event
        self._failure = failure

    def chat(self, _messages) -> str:
        self.calls += 1
        self._events.append(self._event)
        if self._failure is not None:
            raise self._failure
        return "{}"

    def stream_chat(self, _messages) -> str:
        return self.chat(_messages)


class _PreparedDirectFacade:
    def __init__(self, client) -> None:
        self._client = client

    def emit_project(self, _context):
        self._client.chat([{"role": "user", "content": "direct"}])
        return _project("direct")


class _PreparedHisFacade:
    def __init__(self, req2his_client, behavior_client) -> None:
        self._req2his_client = req2his_client
        self._behavior_client = behavior_client
        self.last_skeleton_project = None

    def emit_his(self, _context):
        self._req2his_client.stream_chat([{"role": "user", "content": "his"}])
        return {"schema_version": "system-his-v1.2", "intent": {"design_goal": "counter"}}

    def emit_skeleton_project(self, _context, _system_his):
        self.last_skeleton_project = _project("trusted-skeleton")
        self._behavior_client.stream_chat([{"role": "user", "content": "behavior"}])
        return _project("complete-skeleton-project")


class _PreparedValidationFacade:
    def __init__(self, events: list[str]) -> None:
        self.calls = 0
        self._events = events

    def validate_his(self, _context, _system_his):
        self.calls += 1
        self._events.append("h0-h3")
        return {
            "passed": True,
            **{
                f"h{stage}": {"status": "pass", "diagnostics": []}
                for stage in range(4)
            },
        }


def test_gold_ready_preparation_materializes_three_checkpoints_once(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    context = _context()
    paired_ref = _write_paired_block(
        store, public_projection_sha256=context.public_projection_sha256
    )
    events: list[str] = []
    direct_client = _CountingClient(events, "direct")
    req2his_client = _CountingClient(events, "req2his")
    behavior_client = _CountingClient(events, "behavior")
    ledger = BlockPreparationCostLedger(
        store, paired_block_ref=paired_ref, failure_origin=None
    )
    budget = ModelCallBudget(max_calls=3, attempt_cost_ledger=ledger)
    validation = _PreparedValidationFacade(events)
    pairing = PairingKey(
        paired_block_id="pair-checkpoint-001",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="semantic-checkpoint-001",
        decoding_seed=17,
        model_provenance_sha256="2" * 64,
        replicate_id="replicate-000",
    )

    result = prepare_development_paired_block(
        store,
        paired_block_ref=paired_ref,
        pairing=pairing,
        context=context,
        platform=_platform(),
        facades=BlockPreparationFacades(
            direct=_PreparedDirectFacade(
                budget.client(direct_client, "block_direct_initial")
            ),
            system_his=_PreparedHisFacade(
                budget.client(req2his_client, "block_req2his"),
                budget.client(behavior_client, "block_skeleton_initial"),
            ),
            his_validation=validation,
        ),
        model_budget=budget,
        preparation_policy_sha256="a" * 64,
    )

    assert direct_client.calls == req2his_client.calls == behavior_client.calls == 1
    assert budget.calls_used == 3
    assert events == ["direct", "req2his", "h0-h3", "behavior"]
    assert validation.calls == 1
    assert result.direct_initial_project is not None
    assert result.system_his is not None
    assert result.skeleton_initial_project is not None
    assert result.trusted_skeleton is not None
    assert result.direct_initial_project.artifact_ref.key.endswith(
        "/direct-initial-project"
    )
    assert result.skeleton_initial_project.artifact_ref.key.endswith(
        "/skeleton-initial-project"
    )
    assert (
        result.direct_initial_project.artifact_ref
        != result.skeleton_initial_project.artifact_ref
    )
    assert result.manifest_ref.media_type == "application/json"
    assert read_development_shared_checkpoint_manifest(store, result.manifest_ref)[
        "manifest_status"
    ] == "complete"


@pytest.mark.parametrize(
    ("failed_checkpoint", "blocked", "expected_calls", "expected_statuses"),
    (
        (
            "direct_initial_project",
            {"M0": "direct_initial_project", "M1": "direct_initial_project"},
            {"direct": 1, "req2his": 1, "behavior": 1},
            {
                "direct_initial_project": "failed",
                "shared_system_his": "completed",
                "skeleton_initial_project": "completed",
            },
        ),
        (
            "shared_system_his",
            {
                "M3": "shared_system_his",
                "M4": "shared_system_his",
                "M5": "shared_system_his",
            },
            {"direct": 1, "req2his": 1, "behavior": 0},
            {
                "direct_initial_project": "completed",
                "shared_system_his": "failed",
                "skeleton_initial_project": "not_run",
            },
        ),
        (
            "skeleton_initial_project",
            {
                "M4": "skeleton_initial_project",
                "M5": "skeleton_initial_project",
            },
            {"direct": 1, "req2his": 1, "behavior": 1},
            {
                "direct_initial_project": "completed",
                "shared_system_his": "completed",
                "skeleton_initial_project": "failed",
            },
        ),
    ),
)
def test_checkpoint_failure_blocks_only_verified_manifest_consumers(
    tmp_path,
    failed_checkpoint: str,
    blocked: dict[str, str],
    expected_calls: dict[str, int],
    expected_statuses: dict[str, str],
) -> None:
    store = ArtifactStore(tmp_path / "store")
    context = _context()
    paired_ref = _write_paired_block(
        store, public_projection_sha256=context.public_projection_sha256
    )
    events: list[str] = []
    clients = {
        name: _CountingClient(
            events,
            name,
            failure=(
                RuntimeError(f"synthetic failure at {checkpoint}")
                if checkpoint == failed_checkpoint
                else None
            ),
        )
        for name, checkpoint in (
            ("direct", "direct_initial_project"),
            ("req2his", "shared_system_his"),
            ("behavior", "skeleton_initial_project"),
        )
    }
    ledger = BlockPreparationCostLedger(
        store, paired_block_ref=paired_ref, failure_origin=None
    )
    budget = ModelCallBudget(max_calls=3, attempt_cost_ledger=ledger)
    pairing = PairingKey(
        paired_block_id="pair-checkpoint-001",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="semantic-checkpoint-001",
        decoding_seed=17,
        model_provenance_sha256="2" * 64,
        replicate_id="replicate-000",
    )

    prepared = prepare_development_paired_block(
        store,
        paired_block_ref=paired_ref,
        pairing=pairing,
        context=context,
        platform=_platform(),
        facades=BlockPreparationFacades(
            direct=_PreparedDirectFacade(
                budget.client(clients["direct"], "block_direct_initial")
            ),
            system_his=_PreparedHisFacade(
                budget.client(clients["req2his"], "block_req2his"),
                budget.client(clients["behavior"], "block_skeleton_initial"),
            ),
            his_validation=_PreparedValidationFacade(events),
        ),
        model_budget=budget,
        preparation_policy_sha256="a" * 64,
    )

    manifest = read_development_shared_checkpoint_manifest(
        store, prepared.manifest_ref
    )
    statuses = {
        node["checkpoint_id"]: node["status"] for node in manifest["nodes"]
    }
    replay = replay_development_block_preparation(store, prepared.event_refs)

    assert manifest["manifest_status"] == "incomplete"
    assert statuses == expected_statuses
    assert blocked_methods_from_verified_manifest(
        store, prepared.manifest_ref
    ) == blocked
    assert {name: client.calls for name, client in clients.items()} == expected_calls
    assert replay.actual_axes["logical_model_calls"]["value"] == sum(
        expected_calls.values()
    )
    assert replay.actual_axes["logical_model_calls"]["status"] == "measured"
    assert replay.actual_axes["input_tokens"]["status"] == "unavailable"


def test_complete_resume_validation_is_read_only_and_identity_exact(tmp_path) -> None:
    pairing = PairingKey(
        "pair-checkpoint-001",
        "revision-checkpoint-001",
        "semantic-checkpoint-001",
        17,
        "2" * 64,
        "replicate-000",
    )
    prefix = f"paired/{pairing.digest()}"
    store, paired_block_ref, nodes, event_refs = _fixture(
        tmp_path,
        direct_key=f"{prefix}/direct-initial-project",
        his_key=f"{prefix}/system-his",
        skeleton_key=f"{prefix}/skeleton-initial-project",
        trusted_key=f"{prefix}/trusted-skeleton",
    )
    expected_policy = _expected_preparation_policy(paired_block_ref, prefix=prefix)
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256=expected_policy["preparation_policy_sha256"],
        nodes=nodes,
        block_event_refs=event_refs,
    )
    refs_before = sorted(
        path.relative_to(store.root).as_posix()
        for path in store.root.rglob("*.ref.json")
    )

    first = read_complete_development_shared_checkpoint_resume(
        store,
        manifest_ref,
        expected_preparation_policy=expected_policy,
    )
    second = read_complete_development_shared_checkpoint_resume(
        store,
        manifest_ref,
        expected_preparation_policy=expected_policy,
    )

    assert first == second
    assert sorted(
        path.relative_to(store.root).as_posix()
        for path in store.root.rglob("*.ref.json")
    ) == refs_before


@pytest.mark.parametrize("mismatch", ("paired_block", "policy", "manifest_ref"))
def test_complete_resume_validation_rejects_identity_mismatch(
    tmp_path, mismatch: str
) -> None:
    pairing = PairingKey(
        "pair-checkpoint-001",
        "revision-checkpoint-001",
        "semantic-checkpoint-001",
        17,
        "2" * 64,
        "replicate-000",
    )
    prefix = f"paired/{pairing.digest()}"
    store, paired_block_ref, nodes, event_refs = _fixture(
        tmp_path,
        direct_key=f"{prefix}/direct-initial-project",
        his_key=f"{prefix}/system-his",
        skeleton_key=f"{prefix}/skeleton-initial-project",
        trusted_key=f"{prefix}/trusted-skeleton",
    )
    expected_policy = _expected_preparation_policy(paired_block_ref, prefix=prefix)
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256=expected_policy["preparation_policy_sha256"],
        nodes=nodes,
        block_event_refs=event_refs,
    )
    candidate_manifest = manifest_ref
    if mismatch == "paired_block":
        expected_policy["paired_block_ref"] = replace(
            paired_block_ref, sha256="f" * 64
        ).to_dict()
    elif mismatch == "policy":
        expected_policy["preparation_policy_sha256"] = "f" * 64
    else:
        candidate_manifest = replace(manifest_ref, key="tampered/manifest-ref")

    with pytest.raises(SharedCheckpointResumeError, match="new run ID"):
        read_complete_development_shared_checkpoint_resume(
            store,
            candidate_manifest,
            expected_preparation_policy=expected_policy,
        )


def test_complete_resume_validation_rejects_incomplete_manifest(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _incomplete_direct_fixture(
        tmp_path, event_kind="checkpoint_failed"
    )
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    expected_policy = _expected_preparation_policy(
        paired_block_ref,
        prefix="paired/" + "a" * 64,
    )
    expected_policy["preparation_policy_sha256"] = "3" * 64

    with pytest.raises(SharedCheckpointResumeError, match="new run ID"):
        read_complete_development_shared_checkpoint_resume(
            store,
            manifest_ref,
            expected_preparation_policy=expected_policy,
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
    trusted_key: str = "checkpoints/trusted",
    reuse_direct_as_skeleton: bool = False,
):
    store = ArtifactStore(tmp_path / "store")
    paired_block_ref = _write_paired_block(store)
    artifacts = MethodArtifactGateway(store)
    direct = artifacts.put_project(direct_key, _project("direct"))
    his = artifacts.put_planning(
        his_key, PlanningArtifactKind.SYSTEM_HIS, {"intent": "counter"}
    )
    trusted = artifacts.put_project(trusted_key, _project("trusted"))
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


def _expected_preparation_policy(
    paired_block_ref: ArtifactRef,
    *,
    prefix: str,
    exclusive_model_call_ceilings: dict[str, int] | None = None,
) -> dict:
    policy = {
        "policy_version": "development-block-preparation-policy-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_id": "pair-checkpoint-001",
        "paired_block_ref": paired_block_ref.to_dict(),
        "member_sample_ids": [f"sample-{index}" for index in range(6)],
        "physical_initial_model_call_ceiling": 3,
        "exclusive_model_call_ceilings": (
            dict(exclusive_model_call_ceilings)
            if exclusive_model_call_ceilings is not None
            else {"M0": 0, "M1": 0, "M2": 2, "M3": 1, "M4": 0, "M5": 0}
        ),
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
    policy["preparation_policy_sha256"] = hashlib.sha256(
        json.dumps(
            policy,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return policy


def _rehash_preparation_policy(policy: dict) -> None:
    unsigned = {
        key: value
        for key, value in policy.items()
        if key != "preparation_policy_sha256"
    }
    policy["preparation_policy_sha256"] = hashlib.sha256(
        json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def test_strict_manifest_verifier_anchors_frozen_policy_graph_and_exact_keys(
    tmp_path,
) -> None:
    pairing = PairingKey(
        paired_block_id="pair-checkpoint-001",
        requirement_revision_id="revision-checkpoint-001",
        semantic_instance_id="semantic-checkpoint-001",
        decoding_seed=17,
        model_provenance_sha256="2" * 64,
        replicate_id="replicate-000",
    )
    prefix = f"paired/{pairing.digest()}"
    store, paired_block_ref, nodes, event_refs = _fixture(
        tmp_path,
        direct_key=f"{prefix}/direct-initial-project",
        his_key=f"{prefix}/system-his",
        skeleton_key=f"{prefix}/skeleton-initial-project",
        trusted_key=f"{prefix}/trusted-skeleton",
    )
    expected_policy = _expected_preparation_policy(
        paired_block_ref,
        prefix=prefix,
    )
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256=expected_policy["preparation_policy_sha256"],
        nodes=nodes,
        block_event_refs=event_refs,
    )

    assert verify_development_shared_checkpoint_manifest_against_policy(
        store,
        manifest_ref,
        expected_preparation_policy=expected_policy,
    )["manifest_status"] == "complete"


def test_strict_manifest_verifier_accepts_independently_hashed_override_ceilings(
    tmp_path,
) -> None:
    pairing = PairingKey(
        "pair-checkpoint-001",
        "revision-checkpoint-001",
        "semantic-checkpoint-001",
        17,
        "2" * 64,
        "replicate-000",
    )
    prefix = f"paired/{pairing.digest()}"
    store, paired_block_ref, nodes, event_refs = _fixture(
        tmp_path,
        direct_key=f"{prefix}/direct-initial-project",
        his_key=f"{prefix}/system-his",
        skeleton_key=f"{prefix}/skeleton-initial-project",
        trusted_key=f"{prefix}/trusted-skeleton",
    )
    expected_policy = _expected_preparation_policy(
        paired_block_ref,
        prefix=prefix,
        exclusive_model_call_ceilings={
            "M0": 3,
            "M1": 3,
            "M2": 4,
            "M3": 3,
            "M4": 2,
            "M5": 2,
        },
    )
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256=expected_policy["preparation_policy_sha256"],
        nodes=nodes,
        block_event_refs=event_refs,
    )

    assert verify_development_shared_checkpoint_manifest_against_policy(
        store,
        manifest_ref,
        expected_preparation_policy=expected_policy,
    )["manifest_status"] == "complete"


@pytest.mark.parametrize(
    "mutation",
    ("shape", "bool", "negative", "fractional", "missing", "extra"),
)
def test_strict_manifest_verifier_rejects_invalid_override_ceiling_contract(
    tmp_path,
    mutation: str,
) -> None:
    pairing = PairingKey(
        "pair-checkpoint-001",
        "revision-checkpoint-001",
        "semantic-checkpoint-001",
        17,
        "2" * 64,
        "replicate-000",
    )
    prefix = f"paired/{pairing.digest()}"
    store, paired_block_ref, nodes, event_refs = _fixture(
        tmp_path,
        direct_key=f"{prefix}/direct-initial-project",
        his_key=f"{prefix}/system-his",
        skeleton_key=f"{prefix}/skeleton-initial-project",
        trusted_key=f"{prefix}/trusted-skeleton",
    )
    valid_ceilings = {"M0": 3, "M1": 3, "M2": 4, "M3": 3, "M4": 2, "M5": 2}
    expected_policy = _expected_preparation_policy(
        paired_block_ref,
        prefix=prefix,
        exclusive_model_call_ceilings=valid_ceilings,
    )
    ceilings = expected_policy["exclusive_model_call_ceilings"]
    if mutation == "shape":
        expected_policy["exclusive_model_call_ceilings"] = list(ceilings.values())
    elif mutation == "bool":
        ceilings["M0"] = True
    elif mutation == "negative":
        ceilings["M1"] = -1
    elif mutation == "fractional":
        ceilings["M2"] = 4.5
    elif mutation == "missing":
        ceilings.pop("M5")
    else:
        ceilings["M6"] = 0
    _rehash_preparation_policy(expected_policy)
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256=expected_policy["preparation_policy_sha256"],
        nodes=nodes,
        block_event_refs=event_refs,
    )

    with pytest.raises(ValueError, match="exclusive ceilings"):
        verify_development_shared_checkpoint_manifest_against_policy(
            store,
            manifest_ref,
            expected_preparation_policy=expected_policy,
        )


@pytest.mark.parametrize(
    "mutation",
    ("policy_self_hash", "manifest_policy", "graph", "artifact_key", "trusted_key"),
)
def test_strict_manifest_verifier_rejects_one_factor_policy_and_key_tamper(
    tmp_path,
    mutation: str,
) -> None:
    pairing = PairingKey(
        paired_block_id="pair-checkpoint-001",
        requirement_revision_id="revision-checkpoint-001",
        semantic_instance_id="semantic-checkpoint-001",
        decoding_seed=17,
        model_provenance_sha256="2" * 64,
        replicate_id="replicate-000",
    )
    prefix = f"paired/{pairing.digest()}"
    direct_key = f"{prefix}/direct-initial-project"
    trusted_key = f"{prefix}/trusted-skeleton"
    if mutation == "artifact_key":
        direct_key = "arbitrary/internal/direct-initial-project"
    if mutation == "trusted_key":
        trusted_key = "arbitrary/internal/trusted-skeleton"
    store, paired_block_ref, nodes, event_refs = _fixture(
        tmp_path,
        direct_key=direct_key,
        his_key=f"{prefix}/system-his",
        skeleton_key=f"{prefix}/skeleton-initial-project",
        trusted_key=trusted_key,
    )
    expected_policy = _expected_preparation_policy(
        paired_block_ref,
        prefix=prefix,
    )
    manifest_policy_sha256 = expected_policy["preparation_policy_sha256"]
    if mutation == "manifest_policy":
        manifest_policy_sha256 = "f" * 64
    manifest_ref = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256=manifest_policy_sha256,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    if mutation == "policy_self_hash":
        expected_policy["member_sample_ids"][0] = "tampered-sample"
    elif mutation == "graph":
        expected_policy["expected_checkpoint_graph"][0]["consumer_methods"] = [
            "M0",
            "M2",
        ]
        unsigned = {
            key: value
            for key, value in expected_policy.items()
            if key != "preparation_policy_sha256"
        }
        expected_policy["preparation_policy_sha256"] = hashlib.sha256(
            json.dumps(
                unsigned,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    with pytest.raises(ValueError):
        verify_development_shared_checkpoint_manifest_against_policy(
            store,
            manifest_ref,
            expected_preparation_policy=expected_policy,
        )


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
    ("node_index", "field", "expected"),
    (
        (0, "artifact_ref", "checkpoint artifact reference"),
        (1, "content_sha256", "checkpoint content digest mismatch"),
        (2, "project_package_sha256", "checkpoint project package digest mismatch"),
    ),
    ids=("direct-ref", "his-content", "skeleton-project-package"),
)
def test_verified_manifest_reader_rejects_each_checkpoint_digest_binding_tamper(
    tmp_path, node_index: int, field: str, expected: str
) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)
    reference = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    tampered = json.loads(store.read_verified(reference))
    if field == "artifact_ref":
        tampered["nodes"][node_index][field]["sha256"] = "f" * 64
    else:
        tampered["nodes"][node_index][field] = "f" * 64
    tampered_ref = store.put_blob(
        f"tampered/checkpoint-binding-{node_index}",
        json.dumps(
            tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError, match=expected):
        read_development_shared_checkpoint_manifest(store, tampered_ref)


def test_verified_manifest_reader_rejects_checkpoint_bytes_tamper(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)
    reference = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    artifact_ref = nodes[1].artifact_ref
    assert artifact_ref is not None
    blob_path = store.root / "blobs" / artifact_ref.sha256[:2] / artifact_ref.sha256
    blob_path.write_bytes(b'{"intent":"tampered"}')

    with pytest.raises(ArtifactIntegrityError, match="artifact (size|sha256) mismatch"):
        read_development_shared_checkpoint_manifest(store, reference)


def test_verified_manifest_reader_rejects_cross_block_project_artifact(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)
    reference = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    other_project = MethodArtifactGateway(store).put_project(
        "other/direct-initial-project", _project("other-block")
    )
    tampered = json.loads(store.read_verified(reference))
    tampered["nodes"][0]["artifact_ref"] = other_project.artifact_ref.to_dict()
    tampered["nodes"][0]["content_sha256"] = other_project.artifact_ref.sha256
    tampered["nodes"][0]["project_package_sha256"] = (
        other_project.project_package_sha256
    )
    tampered_ref = store.put_blob(
        "tampered/cross-block-project",
        json.dumps(
            tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError, match="absent from raw event"):
        read_development_shared_checkpoint_manifest(store, tampered_ref)


def test_verified_manifest_reader_rejects_source_event_partition_swap(tmp_path) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)
    reference = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    tampered = json.loads(store.read_verified(reference))
    tampered["nodes"][0]["source_event_refs"] = copy.deepcopy(
        tampered["nodes"][1]["source_event_refs"]
    )
    tampered["nodes"][0]["source_events_sha256"] = tampered["nodes"][1][
        "source_events_sha256"
    ]
    tampered_ref = store.put_blob(
        "tampered/source-event-partition",
        json.dumps(
            tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError, match="source event partition mismatch"):
        read_development_shared_checkpoint_manifest(store, tampered_ref)


def test_verified_manifest_reader_rejects_block_event_set_digest_tamper(
    tmp_path,
) -> None:
    store, paired_block_ref, nodes, event_refs = _fixture(tmp_path)
    reference = write_development_shared_checkpoint_manifest(
        store,
        paired_block_ref=paired_block_ref,
        preparation_policy_sha256="3" * 64,
        nodes=nodes,
        block_event_refs=event_refs,
    )
    tampered = json.loads(store.read_verified(reference))
    tampered["block_events_sha256"] = "f" * 64
    tampered_ref = store.put_blob(
        "tampered/block-event-set-digest",
        json.dumps(
            tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError, match="block event-set digest mismatch"):
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
