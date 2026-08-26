import copy
import hashlib
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.project_contract import (
    build_composite_project_envelope,
    build_project_envelope,
)
from sr2fpga_agent.training_view_exporter import (
    PublicTransitionEvidence,
    build_project_training_view,
    build_transition_training_view,
    validate_training_view_export,
    write_training_view_export,
)
from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.training_pool import (
    build_training_pool_manifest,
    validate_training_pool_exports,
    validate_training_pool_manifest,
)
from sr2fpga_agent.training_release import (
    MANIFEST_FILENAME,
    ReleaseLeakagePolicy,
    build_candidate_training_release,
    validate_training_release_manifest,
    verify_candidate_training_release,
)


def _sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _project(*, increment="1'b1"):
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "direct_counter",
        "top": {
            "module": "direct_top",
            "source": "src/design.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "src/design.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {"toolchain_id": "open_source", "language_standard": "verilog-2005"},
    }
    return GeneratedProject(
        "direct_counter",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "src/design.v": (
                "module direct_top(input wire clk, output reg [7:0] count);\n"
                f"  always @(posedge clk) count <= count + {increment};\n"
                "endmodule\n"
            ),
        },
    )


def _envelope(project, snapshot_id):
    policies = {
        path: {"owner": "model", "origin": "model_generated", "editable": True}
        for path in project.files
    }
    return build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id=snapshot_id,
        file_policies=policies,
    )


def _certificate(initial, terminal, *, eligible=True):
    checks = {
        "training_split_member": True,
        "requirement_ready": True,
        "initial_snapshot_serializable": True,
        "initial_snapshot_pre_feedback": True,
        "qualification_completed_pass": True,
        "trusted_edit_surface_intact": True,
        "method_applicable_h_pass": True,
        "provenance_complete": True,
        "budget_compliant": True,
        "hidden_material_redacted": True,
        "leakage_audit_pass": True,
        "source_policy_allowed": True,
    }
    reasons = []
    if not eligible:
        checks["budget_compliant"] = False
        reasons = ["budget_not_compliant"]
    payload = {
        "contract_version": "training-eligibility-v1",
        "visibility_class": "release_internal",
        "episode_id": "episode-001",
        "method_condition_id": "M0",
        "training_split_id": "train-split-dev",
        "source_class": "model_generated",
        "failure_origin": "natural_llm",
        "policy_id": "development-training-policy",
        "policy_sha256": "b" * 64,
        "episode_pack_sha256": "c" * 64,
        "initial_snapshot_id": "snapshot-initial",
        "initial_snapshot_sha256": initial["envelope_sha256"],
        "terminal_candidate_sha256": "d" * 64,
        "project_envelope_sha256": terminal["envelope_sha256"],
        "qualification_outcome_sha256": "e" * 64,
        "evidence_bundle_sha256": "f" * 64,
        "checks": checks,
        "official_hidden_outcome_ref_count": 0,
        "eligibility_status": "eligible" if eligible else "ineligible",
        "exclusion_reason_ids": reasons,
    }
    return {**payload, "artifact_sha256": _sha256(payload)}


def _fixtures():
    initial_project = _project()
    terminal_project = _project(increment="2'b10")
    initial = _envelope(initial_project, "snapshot-initial")
    terminal = _envelope(terminal_project, "snapshot-final")
    return initial_project, terminal_project, initial, terminal, _certificate(initial, terminal)


def _messages(text="Generate the complete counter project."):
    return [
        {"role": "system", "content": "Return a complete FPGA project."},
        {"role": "user", "content": text},
    ]


def _transition(**overrides):
    values = {
        "public_failure": {"stage": "L2", "reason": "counter mismatch"},
        "public_diagnosis": {"reason": "increment is incorrect"},
        "public_patch": "change the increment to two",
        "public_rerun": {"stage": "L2", "outcome": "pass"},
        "actual_rerun": True,
        "targeted_failure_repaired": True,
        "no_regression": True,
    }
    values.update(overrides)
    return PublicTransitionEvidence(**values)


def test_m6u_and_m6f_use_matched_episode_but_bound_snapshots() -> None:
    initial_project, terminal_project, initial, terminal, certificate = _fixtures()

    m6u, m6u_sidecar = build_project_training_view(
        treatment="M6U",
        eligibility_certificate=certificate,
        project=initial_project,
        project_envelope=initial,
        prompt_messages=_messages(),
    )
    m6f, m6f_sidecar = build_project_training_view(
        treatment="M6F",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages(),
    )

    assert m6u["source_episode_id"] == m6f["source_episode_id"] == "episode-001"
    assert m6u["snapshot_id"] == "snapshot-initial"
    assert m6f["snapshot_id"] == "snapshot-final"
    assert (
        m6u["payload"]["assistant_target"]["files"][0]["content"]
        != m6f["payload"]["assistant_target"]["files"][0]["content"]
    )
    assert m6u_sidecar["snapshot_envelope_sha256"] == initial["envelope_sha256"]
    assert m6f_sidecar["snapshot_envelope_sha256"] == terminal["envelope_sha256"]
    assert all(
        item["path"] != "manifest.json"
        for item in m6f["payload"]["assistant_target"]["files"]
    )


def test_m6u_cannot_use_terminal_snapshot_and_ineligible_certificate_is_rejected() -> None:
    initial_project, terminal_project, initial, terminal, certificate = _fixtures()
    with pytest.raises(ValueError, match="M6U snapshot envelope"):
        build_project_training_view(
            treatment="M6U",
            eligibility_certificate=certificate,
            project=terminal_project,
            project_envelope=terminal,
            prompt_messages=_messages(),
        )

    ineligible = _certificate(initial, terminal, eligible=False)
    with pytest.raises(ValueError, match="eligible certificate"):
        build_project_training_view(
            treatment="M6F",
            eligibility_certificate=ineligible,
            project=terminal_project,
            project_envelope=terminal,
            prompt_messages=_messages(),
        )


@pytest.mark.parametrize(
    "prompt",
    [
        'Generate this project with {"status":"pass"}.',
        'Use {"diagnosis":"counter mismatch"}.',
        'Apply {"patch":"change increment"}.',
        'Include {"verified_pass":true}.',
    ],
)
def test_m6u_rejects_feedback_fields_embedded_in_prompt(prompt) -> None:
    initial_project, _, initial, terminal, certificate = _fixtures()
    with pytest.raises(ValueError, match="forbidden M6U feedback field"):
        build_project_training_view(
            treatment="M6U",
            eligibility_certificate=certificate,
            project=initial_project,
            project_envelope=initial,
            prompt_messages=_messages(prompt),
        )


def test_exporter_rejects_hidden_marker_and_private_canary() -> None:
    _, terminal_project, _, terminal, certificate = _fixtures()
    with pytest.raises(ValueError, match="hidden marker"):
        build_project_training_view(
            treatment="M6F",
            eligibility_certificate=certificate,
            project=terminal_project,
            project_envelope=terminal,
            prompt_messages=_messages("Use official_hidden_outcome."),
        )
    with pytest.raises(ValueError, match="forbidden canary"):
        build_project_training_view(
            treatment="M6F",
            eligibility_certificate=certificate,
            project=terminal_project,
            project_envelope=terminal,
            prompt_messages=_messages("CANARY-PRIVATE-001"),
            forbidden_canaries=("CANARY-PRIVATE-001",),
        )


def test_m6t_requires_complete_actual_transition_and_binds_evidence() -> None:
    _, terminal_project, _, terminal, certificate = _fixtures()
    row, sidecar = build_transition_training_view(
        eligibility_certificate=certificate,
        terminal_project=terminal_project,
        terminal_project_envelope=terminal,
        prompt_messages=_messages(),
        transition=_transition(),
    )

    assert row["treatment"] == "M6T"
    assert row["payload"]["assistant_target"]["kind"] == "public_transition"
    assert sidecar["transition_evidence_sha256"] == _sha256(
        {
            "public_failure": {"stage": "L2", "reason": "counter mismatch"},
            "public_diagnosis": {"reason": "increment is incorrect"},
            "public_patch": "change the increment to two",
            "public_rerun": {"stage": "L2", "outcome": "pass"},
            "actual_rerun": True,
            "targeted_failure_repaired": True,
            "no_regression": True,
        }
    )

    with pytest.raises(ValueError, match="not actually rerun"):
        build_transition_training_view(
            eligibility_certificate=certificate,
            terminal_project=terminal_project,
            terminal_project_envelope=terminal,
            prompt_messages=_messages(),
            transition=_transition(actual_rerun=False),
        )


def test_m6f_e_traj_uses_final_snapshot_without_transition_payload() -> None:
    _, terminal_project, _, terminal, certificate = _fixtures()
    row, sidecar = build_project_training_view(
        treatment="M6F_E_TRAJ",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages(),
        transition=_transition(),
    )

    assert row["treatment"] == "M6F_E_TRAJ"
    assert row["payload"]["assistant_target"]["kind"] == "project_files"
    assert sidecar["transition_evidence_sha256"] == _sha256(
        {
            "public_failure": {"stage": "L2", "reason": "counter mismatch"},
            "public_diagnosis": {"reason": "increment is incorrect"},
            "public_patch": "change the increment to two",
            "public_rerun": {"stage": "L2", "outcome": "pass"},
            "actual_rerun": True,
            "targeted_failure_repaired": True,
            "no_regression": True,
        }
    )


def test_m6f_e_traj_requires_matched_transition() -> None:
    _, terminal_project, _, terminal, certificate = _fixtures()
    with pytest.raises(ValueError, match="matched public transition"):
        build_project_training_view(
            treatment="M6F_E_TRAJ",
            eligibility_certificate=certificate,
            project=terminal_project,
            project_envelope=terminal,
            prompt_messages=_messages(),
        )


def test_row_and_sidecar_tampering_fail_closed() -> None:
    _, terminal_project, _, terminal, certificate = _fixtures()
    row, sidecar = build_project_training_view(
        treatment="M6F",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages(),
    )
    tampered_row = copy.deepcopy(row)
    tampered_row["payload"]["prompt_messages"][1]["content"] = "tampered"
    with pytest.raises(ValueError, match="row_sha256 mismatch"):
        validate_training_view_export(tampered_row, sidecar, certificate)

    tampered_sidecar = {**sidecar, "row_sha256": "0" * 64}
    without_hash = {
        key: value
        for key, value in tampered_sidecar.items()
        if key != "artifact_sha256"
    }
    tampered_sidecar["artifact_sha256"] = _sha256(without_hash)
    with pytest.raises(ValueError, match="binding mismatch: row_sha256"):
        validate_training_view_export(row, tampered_sidecar, certificate)


def test_composite_export_contains_only_model_region(tmp_path) -> None:
    project = _project()
    files = dict(project.files)
    files["src/design.v"] = files["src/design.v"].replace(
        "  always @(posedge clk)",
        "  // SR2FPGA_BEHAVIOR_BEGIN\n  always @(posedge clk)",
    ).replace(
        "endmodule\n",
        "  // SR2FPGA_BEHAVIOR_END\nendmodule\n",
    )
    project = GeneratedProject(project.project_name, files)
    store = ArtifactStore(tmp_path / "events")
    trusted = json.loads(
        store.read_verified(store.append_event("episode-001", "skeleton_built", {}))
    )["event_id"]
    model = json.loads(
        store.read_verified(store.append_event("episode-001", "behavior_generated", {}))
    )["event_id"]
    envelope = build_composite_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M5",
        snapshot_id="snapshot-final",
        trusted_builder_event_id=trusted,
        model_generation_event_id=model,
        event_ref_resolver=store.has_event_id,
    )
    certificate = _certificate(envelope, envelope)
    certificate_without_hash = {
        key: value
        for key, value in certificate.items()
        if key != "artifact_sha256"
    }
    certificate_without_hash["method_condition_id"] = "M5"
    certificate_without_hash["initial_snapshot_id"] = "snapshot-final"
    certificate = {
        **certificate_without_hash,
        "artifact_sha256": _sha256(certificate_without_hash),
    }

    row, _ = build_project_training_view(
        treatment="M6F",
        eligibility_certificate=certificate,
        project=project,
        project_envelope=envelope,
        prompt_messages=_messages(),
        event_ref_resolver=store.has_event_id,
    )

    targets = row["payload"]["assistant_target"]["files"]
    assert len(targets) == 1
    assert targets[0]["role"] == "model_region"
    assert "always @(posedge clk)" in targets[0]["content"]
    assert "module direct_top" not in targets[0]["content"]
    assert "endmodule" not in targets[0]["content"]


def test_writer_atomically_persists_bundle_under_artifacts_only(tmp_path) -> None:
    _, terminal_project, _, terminal, certificate = _fixtures()
    row, sidecar = build_project_training_view(
        treatment="M6F",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages(),
    )
    paths = RepositoryPaths(root=tmp_path)
    output = tmp_path / "artifacts/candidate-releases/cd8/views"

    bundle = write_training_view_export(
        output,
        row=row,
        sidecar=sidecar,
        eligibility_certificate=certificate,
        paths=paths,
    )

    assert bundle.parent == output
    assert json.loads((bundle / "row.json").read_text(encoding="utf-8")) == row
    assert json.loads(
        (bundle / "eligibility-sidecar.json").read_text(encoding="utf-8")
    ) == sidecar
    assert not list(output.glob(".staging-*"))
    with pytest.raises(FileExistsError, match="already exists"):
        write_training_view_export(
            output,
            row=row,
            sidecar=sidecar,
            eligibility_certificate=certificate,
            paths=paths,
        )


@pytest.mark.parametrize("relative", ["datasets/release", "outside"])
def test_writer_rejects_non_artifacts_destinations_before_creating_files(
    tmp_path, relative
) -> None:
    _, terminal_project, _, terminal, certificate = _fixtures()
    row, sidecar = build_project_training_view(
        treatment="M6F",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages(),
    )
    target = tmp_path / relative

    with pytest.raises(ValueError, match="only under artifacts"):
        write_training_view_export(
            target,
            row=row,
            sidecar=sidecar,
            eligibility_certificate=certificate,
            paths=RepositoryPaths(root=tmp_path),
        )

    assert not target.exists()


def _matched_exports(*, endpoint_transition=None):
    initial_project, terminal_project, initial, terminal, certificate = _fixtures()
    m6u = build_project_training_view(
        treatment="M6U",
        eligibility_certificate=certificate,
        project=initial_project,
        project_envelope=initial,
        prompt_messages=_messages(),
    )
    m6f = build_project_training_view(
        treatment="M6F",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages(),
    )
    transition = _transition()
    m6t = build_transition_training_view(
        eligibility_certificate=certificate,
        terminal_project=terminal_project,
        terminal_project_envelope=terminal,
        prompt_messages=_messages(),
        transition=transition,
    )
    endpoint = build_project_training_view(
        treatment="M6F_E_TRAJ",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages(),
        transition=endpoint_transition or transition,
    )
    return {
        "M6U": [(*m6u, certificate)],
        "M6F": [(*m6f, certificate)],
        "M6T": [(*m6t, certificate)],
        "M6F_E_TRAJ": [(*endpoint, certificate)],
    }


def test_pool_builder_matches_e_final_e_traj_and_mixture() -> None:
    exports = _matched_exports()
    manifest = build_training_pool_manifest(
        exports=exports,
        family_by_episode={"episode-001": "counter"},
    )

    assert manifest["e_final_episode_ids"] == ["episode-001"]
    assert manifest["e_traj_episode_ids"] == ["episode-001"]
    assert manifest["mixture_strata"] == [
        {
            "family_id": "counter",
            "source_class": "model_generated",
            "failure_origin": "natural_llm",
            "episode_ids": ["episode-001"],
            "episode_count": 1,
        }
    ]
    validate_training_pool_manifest(manifest)
    validate_training_pool_exports(manifest, exports)


def test_pool_builder_rejects_unmatched_treatment_episode_sets() -> None:
    exports = _matched_exports()
    exports["M6F"] = []
    with pytest.raises(ValueError, match="M6U and M6F episode IDs"):
        build_training_pool_manifest(
            exports=exports,
            family_by_episode={"episode-001": "counter"},
        )


def test_pool_builder_rejects_transition_mismatch() -> None:
    exports = _matched_exports(
        endpoint_transition=_transition(public_patch="a different valid patch")
    )
    with pytest.raises(ValueError, match="transition evidence mismatch"):
        build_training_pool_manifest(
            exports=exports,
            family_by_episode={"episode-001": "counter"},
        )


def test_pool_builder_requires_exact_family_coverage() -> None:
    with pytest.raises(ValueError, match="family assignments"):
        build_training_pool_manifest(
            exports=_matched_exports(),
            family_by_episode={},
        )


def test_pool_manifest_and_artifact_reconciliation_fail_on_tampering() -> None:
    exports = _matched_exports()
    manifest = build_training_pool_manifest(
        exports=exports,
        family_by_episode={"episode-001": "counter"},
    )
    tampered = copy.deepcopy(manifest)
    tampered["mixture_strata"][0]["episode_count"] = 2
    without_hash = {key: value for key, value in tampered.items() if key != "artifact_sha256"}
    tampered["artifact_sha256"] = _sha256(without_hash)
    with pytest.raises(ValueError, match="mixture stratum"):
        validate_training_pool_manifest(tampered)

    swapped = copy.deepcopy(exports)
    row, sidecar, certificate = swapped["M6F"][0]
    forged_sidecar = copy.deepcopy(sidecar)
    forged_sidecar["artifact_sha256"] = "0" * 64
    swapped["M6F"][0] = (row, forged_sidecar, certificate)
    with pytest.raises(ValueError, match="sidecar artifact_sha256"):
        validate_training_pool_exports(manifest, swapped)

    forged_policy = copy.deepcopy(manifest)
    forged_policy["policy_id"] = "different-policy"
    without_hash = {
        key: value
        for key, value in forged_policy.items()
        if key != "artifact_sha256"
    }
    forged_policy["artifact_sha256"] = _sha256(without_hash)
    validate_training_pool_manifest(forged_policy)
    with pytest.raises(ValueError, match="policy does not match"):
        validate_training_pool_exports(forged_policy, exports)


def test_pool_manifest_rejects_noncanonical_pool_identity() -> None:
    manifest = build_training_pool_manifest(
        exports=_matched_exports(),
        family_by_episode={"episode-001": "counter"},
    )
    manifest["pool_id"] = "pool-forged"
    without_hash = {
        key: value for key, value in manifest.items() if key != "artifact_sha256"
    }
    manifest["artifact_sha256"] = _sha256(without_hash)

    with pytest.raises(ValueError, match="pool_id is not canonical"):
        validate_training_pool_manifest(manifest)


def _candidate_release_inputs(*, include_traj=True):
    exports = _matched_exports()
    if not include_traj:
        exports["M6T"] = []
        exports["M6F_E_TRAJ"] = []
    pool = build_training_pool_manifest(
        exports=exports,
        family_by_episode={"episode-001": "counter"},
    )
    policy = ReleaseLeakagePolicy.create(
        policy_id="candidate-leakage-policy",
        forbidden_canaries=("CANARY-RELEASE-PRIVATE",),
    )
    return exports, pool, policy


@pytest.mark.parametrize("include_traj", [True, False])
def test_candidate_release_builds_and_verifies_without_training_authority(
    tmp_path, include_traj
) -> None:
    exports, pool, policy = _candidate_release_inputs(include_traj=include_traj)
    paths = RepositoryPaths(root=tmp_path)
    output = tmp_path / "artifacts/training-candidate-releases"

    release = build_candidate_training_release(
        output,
        pool_manifest=pool,
        exports=exports,
        leakage_policy=policy,
        paths=paths,
    )
    manifest = verify_candidate_training_release(
        release,
        leakage_policy=policy,
        paths=paths,
    )

    assert manifest["release_state"] == "candidate_unpromoted"
    assert manifest["training_authorized"] is False
    assert "authorization" not in manifest
    assert manifest["official_hidden_outcome_reference_count"] == 0
    assert not list(output.glob(".staging-*"))
    m6t = next(item for item in manifest["treatments"] if item["treatment"] == "M6T")
    assert m6t["row_count"] == (1 if include_traj else 0)


def test_candidate_release_rejects_non_artifacts_path_without_writes(tmp_path) -> None:
    exports, pool, policy = _candidate_release_inputs()
    target = tmp_path / "datasets/release"

    with pytest.raises(ValueError, match="only under artifacts"):
        build_candidate_training_release(
            target,
            pool_manifest=pool,
            exports=exports,
            leakage_policy=policy,
            paths=RepositoryPaths(root=tmp_path),
        )

    assert not target.exists()


def test_candidate_release_rejects_checksum_and_inventory_tampering(tmp_path) -> None:
    exports, pool, policy = _candidate_release_inputs()
    paths = RepositoryPaths(root=tmp_path)
    release = build_candidate_training_release(
        tmp_path / "artifacts/releases",
        pool_manifest=pool,
        exports=exports,
        leakage_policy=policy,
        paths=paths,
    )
    view = release / "views/M6F.jsonl"
    view.write_text(view.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="size mismatch|checksum mismatch"):
        verify_candidate_training_release(
            release, leakage_policy=policy, paths=paths
        )

    view.write_bytes(
        next(
            record
            for record in json.loads((release / MANIFEST_FILENAME).read_text(encoding="utf-8"))[
                "release_files"
            ]
            if record["path"] == "views/M6F.jsonl"
        )["sha256"].encode("ascii")
    )
    (release / "extra.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory mismatch"):
        verify_candidate_training_release(
            release, leakage_policy=policy, paths=paths
        )


def test_candidate_release_rechecks_forbidden_canaries_before_creation(tmp_path) -> None:
    initial_project, terminal_project, initial, terminal, certificate = _fixtures()
    row, sidecar = build_project_training_view(
        treatment="M6F",
        eligibility_certificate=certificate,
        project=terminal_project,
        project_envelope=terminal,
        prompt_messages=_messages("CANARY-LATE-AUDIT"),
    )
    exports = _matched_exports()
    exports["M6F"] = [(row, sidecar, certificate)]
    pool = build_training_pool_manifest(
        exports=exports,
        family_by_episode={"episode-001": "counter"},
    )
    policy = ReleaseLeakagePolicy.create(
        policy_id="late-audit-policy",
        forbidden_canaries=("CANARY-LATE-AUDIT",),
    )
    target = tmp_path / "artifacts/releases"

    with pytest.raises(ValueError, match="forbidden canary"):
        build_candidate_training_release(
            target,
            pool_manifest=pool,
            exports=exports,
            leakage_policy=policy,
            paths=RepositoryPaths(root=tmp_path),
        )

    assert not target.exists()


def test_candidate_verifier_requires_expected_policy_and_rejects_promoted(tmp_path) -> None:
    exports, pool, policy = _candidate_release_inputs()
    paths = RepositoryPaths(root=tmp_path)
    release = build_candidate_training_release(
        tmp_path / "artifacts/releases",
        pool_manifest=pool,
        exports=exports,
        leakage_policy=policy,
        paths=paths,
    )
    other_policy = ReleaseLeakagePolicy.create(policy_id="other-policy")
    with pytest.raises(ValueError, match="leakage policy mismatch"):
        verify_candidate_training_release(
            release,
            leakage_policy=other_policy,
            paths=paths,
        )

    manifest_path = release / MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["release_state"] = "promoted"
    manifest["training_authorized"] = True
    manifest["authorization"] = {
        "campaign_freeze_sha256": "a" * 64,
        "training_plan_sha256": "b" * 64,
        "promotion_record_sha256": "c" * 64,
    }
    without_hash = {
        key: value for key, value in manifest.items() if key != "artifact_sha256"
    }
    manifest["artifact_sha256"] = _sha256(without_hash)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    validate_training_release_manifest(manifest)
    with pytest.raises(ValueError, match="rejects promoted"):
        verify_candidate_training_release(
            release,
            leakage_policy=policy,
            paths=paths,
        )
