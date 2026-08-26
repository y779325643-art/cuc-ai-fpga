import json

import pytest

from sr2fpga_agent.agent import (
    _RequirementBoundaryMetadataError,
    _requirement_boundary_stop,
)
from sr2fpga_agent.artifact_store import (
    ArtifactConflictError,
    ArtifactIntegrityError,
    ArtifactStore,
    BudgetReservationError,
    EpisodeBudgetLedger,
    OneShotViolation,
)
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.frozen_context import (
    build_development_episode_pack,
    freeze_ready_requirement_context,
    validate_episode_pack,
)
from sr2fpga_agent.method_contract import (
    HStageApplicability,
    MethodConditionId,
    ModelStageId,
    method_contract,
)
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.project_contract import build_project_envelope
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary


def _platform() -> PlatformProfile:
    return PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )


def _ready_decision():
    return evaluate_requirement_boundary(
        ProjectRequest(
            task_type="counter",
            width=8,
            project_name="counter8",
            description="Build an 8-bit synchronous counter with active-low reset.",
        ),
        _platform(),
    )


def _canonical_project() -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "counter8",
        "top": {
            "module": "top",
            "source": "rtl/design.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "rtl/design.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    return GeneratedProject(
        "counter8",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "rtl/design.v": "module top(input clk, output [7:0] count); endmodule\n",
        },
    )


def _contains(value, needle: str) -> bool:
    if isinstance(value, dict):
        return any(_contains(key, needle) or _contains(item, needle) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains(item, needle) for item in value)
    return needle in value if isinstance(value, str) else False


def test_manifest_resolver_loads_registered_episode_pack_schema() -> None:
    contract = ContractRegistry().load_schema("episode_pack")

    assert contract.version == "episode-pack-v1"
    assert contract.path.name == "episode-pack-v1.schema.json"
    with pytest.raises(KeyError, match="unregistered contract"):
        ContractRegistry().load_schema("not_registered")


def test_ready_context_hash_is_method_neutral_and_hides_evaluator_metadata() -> None:
    context = freeze_ready_requirement_context(_ready_decision(), _platform())
    canary = "PRIVATE-CANARY-DO-NOT-EXPOSE"
    m0 = build_development_episode_pack(
        context,
        episode_id="episode-m0",
        analysis_population="development",
        method_condition="M0",
        evaluator_metadata={"family_id": "counter-family", "canary": canary},
        private_ref_ids=("oracle:counter-001",),
    )
    m4 = build_development_episode_pack(
        context,
        episode_id="episode-m4",
        analysis_population="development",
        method_condition="M4",
        evaluator_metadata={"family_id": "counter-family", "canary": canary},
        private_ref_ids=("oracle:counter-001",),
    )

    assert m0.context.public_projection_sha256 == m4.context.public_projection_sha256
    assert m0.generation_visible() == m4.generation_visible()
    assert not _contains(m0.generation_visible(), canary)
    assert not _contains(m0.generation_visible(), "counter-family")
    assert "declared_task_type" not in {
        fact["fact_id"] for fact in m0.generation_visible()["fact_records"]
    }
    assert validate_episode_pack(m0.to_dict()) == ()


def test_non_ready_requirement_cannot_be_frozen() -> None:
    decision = evaluate_requirement_boundary(
        ProjectRequest(
            task_type="unclassified",
            width=8,
            project_name="ambiguous",
            description="Build an 8-bit counter with a host interface.",
        ),
        _platform(),
    )

    assert decision.disposition == "needs_clarification"
    with pytest.raises(ValueError, match="only a ready"):
        freeze_ready_requirement_context(decision, _platform())


def test_episode_pack_detects_public_or_audit_tampering() -> None:
    context = freeze_ready_requirement_context(_ready_decision(), _platform())
    payload = build_development_episode_pack(
        context,
        episode_id="episode-001",
        analysis_population="excluded",
        method_condition="M0",
        evaluator_metadata={},
    ).to_dict()
    payload["public_context"]["public_text"] = "changed after freeze"

    errors = validate_episode_pack(payload)

    assert any("public_projection_sha256" in error for error in errors)
    assert any("pack_sha256" in error for error in errors)


def test_development_builder_cannot_create_an_unsigned_official_pack() -> None:
    context = freeze_ready_requirement_context(_ready_decision(), _platform())

    with pytest.raises(ValueError, match="signed G4b loader"):
        build_development_episode_pack(
            context,
            episode_id="official-001",
            analysis_population="official",
            method_condition="M0",
            evaluator_metadata={},
        )


def test_runtime_boundary_rejects_a_tampered_ready_pack_before_generation() -> None:
    decision = _ready_decision()
    context = freeze_ready_requirement_context(decision, _platform())
    pack = build_development_episode_pack(
        context,
        episode_id="episode-001",
        analysis_population="development",
        method_condition="M0",
        evaluator_metadata={},
    ).to_dict()
    pack["public_context"]["public_text"] = "tampered"

    with pytest.raises(_RequirementBoundaryMetadataError, match="episode_pack metadata is invalid"):
        _requirement_boundary_stop(
            {
                "requirement_boundary": decision.to_dict(),
                "episode_pack": pack,
            }
        )


def test_method_contracts_close_applicability_and_repair_privileges() -> None:
    assert method_contract("M0").emits_system_his is False
    assert method_contract("M0").h_stage_applicability is HStageApplicability.NOT_APPLICABLE
    assert method_contract("M1").allows_project_repair is True
    assert method_contract("M1").declared_model_stages == (
        ModelStageId.DIRECT_PROJECT,
        ModelStageId.PROJECT_REPAIR,
    )
    assert method_contract("M3").uses_deterministic_skeleton is False
    assert method_contract("M4").allows_project_repair is False
    assert method_contract("M5").allows_his_correction is True
    assert method_contract(MethodConditionId.M5).allows_project_repair is True
    assert set(method_contract("M5").model_visible_field_ids) == set(
        freeze_ready_requirement_context(_ready_decision(), _platform()).to_dict()
    )
    with pytest.raises(KeyError, match="unknown method condition"):
        method_contract("M7")


def test_artifact_store_is_idempotent_per_key_and_rejects_conflicts(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")

    first = store.put_blob("objects/design", b"first")
    assert store.put_blob("objects/design", b"first") == first
    assert store.read_verified("objects/design") == b"first"
    with pytest.raises(ArtifactConflictError, match="different content"):
        store.put_blob("objects/design", b"second")


def test_artifact_store_detects_blob_tampering(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = store.put_blob("objects/design", b"trusted")
    blob = store.root / "blobs" / reference.sha256[:2] / reference.sha256
    blob.write_bytes(b"tampered")

    with pytest.raises(ArtifactIntegrityError, match="mismatch"):
        store.read_verified(reference)


def test_artifact_store_resolves_only_content_verified_event_ids(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = store.append_event("episode-001", "candidate_created", {})
    event_id = json.loads(store.read_verified(reference))["event_id"]

    assert store.has_event_id(event_id) is True
    assert store.has_event_id("event-" + "f" * 64) is False
    blob = store.root / "blobs" / reference.sha256[:2] / reference.sha256
    blob.write_bytes(b"tampered")
    assert store.has_event_id(event_id) is False


def test_validated_pack_candidate_seal_and_one_shot_are_write_once(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    context = freeze_ready_requirement_context(_ready_decision(), _platform())
    pack = build_development_episode_pack(
        context,
        episode_id="episode-001",
        analysis_population="development",
        method_condition="M0",
        evaluator_metadata={},
    )
    pack_ref = store.put_validated_json(
        "packs/episode-001",
        pack.to_dict(),
        contract_key="episode_pack",
    )
    assert json.loads(store.read_verified(pack_ref))["pack_sha256"] == pack.pack_sha256

    project = _canonical_project()
    policies = {
        path: {"owner": "model", "origin": "model_generated", "editable": True}
        for path in project.files
    }
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=policies,
    )
    envelope_ref = store.put_validated_json(
        "envelopes/candidate-001",
        envelope,
        contract_key="project_envelope",
    )
    event_ref = store.append_event("episode-001", "candidate_created", {})
    seal_ref = store.seal_candidate(
        "candidate-001",
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256=context.public_projection_sha256,
        creation_event_ref=event_ref,
    )
    seal = json.loads(store.read_verified(seal_ref))
    assert seal["candidate_id"] == "candidate-001"
    assert {record["path"] for record in seal["project_files"]} == set(project.files)
    rtl_record = next(
        record for record in seal["project_files"] if record["path"] == "rtl/design.v"
    )
    assert store.read_verified(rtl_record["artifact_key"]) == project.files[
        "rtl/design.v"
    ].encode("utf-8")
    project.files["rtl/design.v"] = "mutated after seal\n"
    restored = store.read_sealed_project(seal_ref)
    assert restored.files["rtl/design.v"] != project.files["rtl/design.v"]
    assert restored.files["rtl/design.v"].startswith("module top")

    store.consume_once("official-hidden-episode-001", seal_ref.sha256)
    with pytest.raises(OneShotViolation, match="already consumed"):
        store.consume_once("official-hidden-episode-001", seal_ref.sha256)


def test_candidate_seal_rejects_project_mutation_and_cross_episode_event(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    project = _canonical_project()
    policies = {
        path: {"owner": "model", "origin": "model_generated", "editable": True}
        for path in project.files
    }
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=policies,
    )
    envelope_ref = store.put_validated_json(
        "envelopes/candidate-001", envelope, contract_key="project_envelope"
    )
    creation = store.append_event("episode-001", "candidate_created", {})
    files = dict(project.files)
    files["rtl/design.v"] += "// tampered\n"

    with pytest.raises(ValueError, match="does not match terminal candidate"):
        store.seal_candidate(
            "candidate-mutated",
            project=GeneratedProject(project.project_name, files),
            project_envelope_ref=envelope_ref,
            requirement_projection_sha256="b" * 64,
            creation_event_ref=creation,
        )

    wrong_episode = store.append_event("episode-002", "candidate_created", {})
    with pytest.raises(ValueError, match="episode IDs differ"):
        store.seal_candidate(
            "candidate-wrong-event",
            project=project,
            project_envelope_ref=envelope_ref,
            requirement_projection_sha256="b" * 64,
            creation_event_ref=wrong_episode,
        )


def test_public_evaluation_candidate_seals_exact_attempt_before_evaluation(
    tmp_path,
) -> None:
    store = ArtifactStore(tmp_path / "store")
    project = _canonical_project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-public-001",
        method_condition_id="M2",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-public-001",
        file_policies={
            path: {"owner": "model", "origin": "model_generated", "editable": False}
            for path in project.files
        },
    )
    envelope_ref = store.put_validated_json(
        "envelopes/public-candidate-001",
        envelope,
        contract_key="project_envelope",
    )
    creation_ref = store.append_event(
        "episode-public-001",
        "candidate_created",
        {
            "candidate_id": "public-candidate-001",
            "attempt_id": "attempt-001",
            "method_condition_id": "M2",
        },
    )

    seal_ref = store.seal_public_evaluation_candidate(
        "public-candidate-001",
        attempt_id="attempt-001",
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256="b" * 64,
        creation_event_ref=creation_ref,
    )
    seal = json.loads(store.read_verified(seal_ref))

    assert seal["seal_stage"] == "pre_public_evaluation"
    assert seal["terminal_status"] == "unselected_at_seal"
    assert seal["pass_credit_authority"] is False
    assert seal["attempt_id"] == "attempt-001"
    assert seal["project_envelope_ref"]["artifact_key"] == envelope_ref.key
    assert seal["project_envelope_ref"]["sha256"] == envelope_ref.sha256
    assert seal["creation_event_ref"]["artifact_key"] == creation_ref.key

    project.files["rtl/design.v"] = "mutated after public seal\n"
    restored = store.read_public_evaluation_candidate(seal_ref)
    assert restored.files["rtl/design.v"].startswith("module top")


def test_public_evaluation_candidate_fails_closed_on_identity_and_ref_tamper(
    tmp_path,
) -> None:
    store = ArtifactStore(tmp_path / "store")
    project = _canonical_project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-public-002",
        method_condition_id="M3",
        method_policy_sha256="c" * 64,
        snapshot_id="snapshot-public-002",
        file_policies={
            path: {"owner": "model", "origin": "model_generated", "editable": False}
            for path in project.files
        },
    )
    envelope_ref = store.put_validated_json(
        "envelopes/public-candidate-002",
        envelope,
        contract_key="project_envelope",
    )
    wrong_identity_ref = store.append_event(
        "episode-public-002",
        "candidate_created",
        {
            "candidate_id": "public-candidate-002",
            "attempt_id": "attempt-wrong",
            "method_condition_id": "M3",
        },
    )
    with pytest.raises(ValueError, match="attempt_id does not match"):
        store.seal_public_evaluation_candidate(
            "public-candidate-002",
            attempt_id="attempt-002",
            project=project,
            project_envelope_ref=envelope_ref,
            requirement_projection_sha256="d" * 64,
            creation_event_ref=wrong_identity_ref,
        )

    creation_ref = store.append_event(
        "episode-public-002",
        "candidate_created",
        {
            "candidate_id": "public-candidate-002",
            "attempt_id": "attempt-002",
            "method_condition_id": "M3",
        },
    )
    seal_ref = store.seal_public_evaluation_candidate(
        "public-candidate-002",
        attempt_id="attempt-002",
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256="d" * 64,
        creation_event_ref=creation_ref,
    )
    envelope_blob = (
        store.root / "blobs" / envelope_ref.sha256[:2] / envelope_ref.sha256
    )
    envelope_blob.write_bytes(b"tampered")
    with pytest.raises(ArtifactIntegrityError, match="artifact size mismatch"):
        store.read_public_evaluation_candidate(seal_ref)


def test_minimal_budget_reservations_are_append_only_and_fail_closed(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    budget = EpisodeBudgetLedger(store, "episode-001", {"model_calls": 2})

    first = budget.reserve("model_calls")
    second = budget.reserve("model_calls")

    assert first.key != second.key
    assert budget.summary()["model_calls"] == {"limit": 2, "used": 2, "remaining": 0}
    with pytest.raises(BudgetReservationError, match="budget exhausted"):
        budget.reserve("model_calls")
