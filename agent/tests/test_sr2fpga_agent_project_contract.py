import copy
import hashlib
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.project_contract import (
    build_composite_project_envelope,
    build_project_envelope,
    validate_project_envelope,
    validate_project_package_manifest,
    verify_project_envelope,
)


def _canonical_project() -> GeneratedProject:
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
            {
                "path": "src/design.v",
                "role": "rtl_source",
                "language": "verilog",
            }
        ],
        "artifacts": [],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    return GeneratedProject(
        project_name="direct_counter",
        files={
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "src/design.v": (
                "module direct_top(input wire clk, output reg [7:0] count);\n"
                "  always @(posedge clk) count <= count + 1'b1;\n"
                "endmodule\n"
            ),
        },
    )


def _model_owned_policies(project: GeneratedProject) -> dict[str, dict[str, object]]:
    return {
        path: {
            "owner": "model",
            "origin": "model_generated",
            "editable": True,
        }
        for path in project.files
    }


def _composite_envelope(tmp_path):
    project = _canonical_project()
    files = dict(project.files)
    files["src/design.v"] = files["src/design.v"].replace(
        "  always @(posedge clk)",
        "  // SR2FPGA_BEHAVIOR_BEGIN\n  always @(posedge clk)",
    ).replace(
        "endmodule\n",
        "  // SR2FPGA_BEHAVIOR_END\nendmodule\n",
    )
    project = GeneratedProject(project.project_name, files)
    store = ArtifactStore(tmp_path / "event-store")
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
        snapshot_id="snapshot-000",
        trusted_builder_event_id=trusted,
        model_generation_event_id=model,
        event_ref_resolver=store.has_event_id,
    )
    return project, store, envelope


def test_canonical_minimal_project_and_trusted_envelope_validate() -> None:
    project = _canonical_project()
    manifest = json.loads(project.files["manifest.json"])

    assert validate_project_package_manifest(manifest) == []

    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(project),
    )

    assert validate_project_envelope(envelope) == []
    assert verify_project_envelope(project, envelope) == []
    assert envelope["integrity_scheme"] == (
        "sr2fpga-json-sortkeys-merkle-sha256-v1"
    )
    assert envelope["files"][0]["file_role"] == "project_manifest"
    assert envelope["files"][1]["file_role"] == "rtl_source"
    assert envelope["files"][1]["sha256"] == hashlib.sha256(
        project.files["src/design.v"].encode("utf-8")
    ).hexdigest()
    assert "envelope_sha256" in envelope
    assert len(envelope["project_merkle_root_sha256"]) == 64


def test_project_envelope_integrity_golden_vector() -> None:
    project = _canonical_project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(project),
    )

    assert envelope["project_package_sha256"] == (
        "90176ac6d296288739a55819a172267d53e6622f344f67e503058b48c5078390"
    )
    assert envelope["project_merkle_root_sha256"] == (
        "b9b699894c00115b14b4b564f3ce64a8ff84d1f096ceb18c099fa54d27152828"
    )
    assert envelope["envelope_sha256"] == (
        "7e67449c6c3a1f27fc251efda625c4652964cddb6c87f4e583ccf005cbd1e2ab"
    )


def test_project_envelope_requires_explicit_policy_for_every_file() -> None:
    project = _canonical_project()

    with pytest.raises(ValueError, match="missing project paths: src/design.v"):
        build_project_envelope(
            project,
            episode_id="episode-001",
            method_condition_id="M0",
            method_policy_sha256="a" * 64,
            snapshot_id="snapshot-000",
            file_policies={"manifest.json": _model_owned_policies(project)["manifest.json"]},
        )


def test_project_envelope_rejects_undeclared_project_file() -> None:
    project = _canonical_project()
    project.files["notes.txt"] = "candidate note\n"

    with pytest.raises(
        ValueError,
        match="project-package-v1 does not declare project paths: notes.txt",
    ):
        build_project_envelope(
            project,
            episode_id="episode-001",
            method_condition_id="M0",
            method_policy_sha256="a" * 64,
            snapshot_id="snapshot-000",
            file_policies=_model_owned_policies(project),
        )


def test_project_envelope_rejects_evaluator_material_until_cd3_authority() -> None:
    project = _canonical_project()

    with pytest.raises(ValueError, match="require CD3 trusted authority"):
        build_project_envelope(
            project,
            episode_id="episode-001",
            method_condition_id="M0",
            method_policy_sha256="a" * 64,
            snapshot_id="snapshot-000",
            file_policies=_model_owned_policies(project),
            evaluator_material_refs=[
                {
                    "opaque_ref_id": "hidden-oracle-001",
                    "kind": "oracle",
                    "commitment_sha256": "b" * 64,
                }
            ],
        )


def test_project_envelope_rejects_composite_until_cd3_authority() -> None:
    project = _canonical_project()
    policies = _model_owned_policies(project)
    policies["src/design.v"] = {
        "owner": "composite",
        "origin": "deterministic",
        "editable": True,
        "regions": [
            {
                "region_id": "trusted-shell",
                "owner": "trusted_builder",
                "sha256": "b" * 64,
                "editable": False,
                "event_refs": ["event-compose-001"],
            },
            {
                "region_id": "model-behavior",
                "owner": "model",
                "sha256": "c" * 64,
                "editable": True,
                "event_refs": ["event-generate-001"],
            },
        ],
    }

    with pytest.raises(ValueError, match="require CD3 trusted authority"):
        build_project_envelope(
            project,
            episode_id="episode-001",
            method_condition_id="M4",
            method_policy_sha256="a" * 64,
            snapshot_id="snapshot-000",
            file_policies=policies,
        )


def test_project_envelope_validation_detects_tampered_file_tree() -> None:
    project = _canonical_project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(project),
    )
    tampered = copy.deepcopy(envelope)
    tampered["files"][1]["sha256"] = "f" * 64

    errors = validate_project_envelope(tampered)

    assert any("envelope_sha256" in error for error in errors)
    assert any("project_merkle_root_sha256" in error for error in errors)


def test_project_package_digest_changes_when_rtl_changes() -> None:
    project = _canonical_project()
    original = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(project),
    )
    changed_files = dict(project.files)
    changed_files["src/design.v"] += "// changed implementation\n"
    changed_project = GeneratedProject(
        project_name=project.project_name,
        files=changed_files,
    )
    changed = build_project_envelope(
        changed_project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(changed_project),
    )

    assert changed["project_merkle_root_sha256"] != (
        original["project_merkle_root_sha256"]
    )
    assert changed["project_package_sha256"] != original["project_package_sha256"]


def test_verifier_detects_project_mutation_after_envelope_build() -> None:
    project = _canonical_project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(project),
    )
    mutated_files = dict(project.files)
    mutated_files["src/design.v"] += "// mutation after seal\n"
    mutated_project = GeneratedProject(project.project_name, mutated_files)

    assert validate_project_envelope(envelope) == []
    errors = verify_project_envelope(mutated_project, envelope)

    assert any("does not match project bytes" in error for error in errors)
    assert any("does not match current project bytes" in error for error in errors)
    assert any("does not match manifest and current project root" in error for error in errors)


def test_verifier_requires_the_exact_project_path_set() -> None:
    project = _canonical_project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(project),
    )

    missing_source = GeneratedProject(
        project_name=project.project_name,
        files={"manifest.json": project.files["manifest.json"]},
    )
    assert any(
        "records reference unknown project paths: src/design.v" in error
        for error in verify_project_envelope(missing_source, envelope)
    )

    added_file = GeneratedProject(
        project_name=project.project_name,
        files={**project.files, "notes.txt": "added after envelope build\n"},
    )
    assert any(
        "missing records for project paths: notes.txt" in error
        for error in verify_project_envelope(added_file, envelope)
    )

    wrong_role = copy.deepcopy(envelope)
    wrong_role["files"][1]["file_role"] = "helper"
    assert any(
        "file_role: does not match project manifest" in error
        for error in verify_project_envelope(project, wrong_role)
    )


def test_envelope_rejects_runtime_unsafe_and_casefold_colliding_paths() -> None:
    project = _canonical_project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="a" * 64,
        snapshot_id="snapshot-000",
        file_policies=_model_owned_policies(project),
    )
    unsafe = copy.deepcopy(envelope)
    unsafe["files"][1]["path"] = "src/design:alternate.v"
    assert any(
        "unsafe project file path" in error
        for error in validate_project_envelope(unsafe)
    )

    manifest = json.loads(project.files["manifest.json"])
    manifest["artifacts"] = [
        {
            "path": "src/Design.v",
            "role": "helper",
            "applicability": "advisory",
        }
    ]
    collision_project = GeneratedProject(
        project_name=project.project_name,
        files={
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "src/design.v": project.files["src/design.v"],
            "src/Design.v": "casefold collision\n",
        },
    )
    with pytest.raises(ValueError, match="casefold-colliding paths"):
        build_project_envelope(
            collision_project,
            episode_id="episode-001",
            method_condition_id="M0",
            method_policy_sha256="a" * 64,
            snapshot_id="snapshot-000",
            file_policies=_model_owned_policies(collision_project),
        )


def test_trusted_composite_envelope_binds_region_bytes_events_and_policy(tmp_path) -> None:
    project, store, envelope = _composite_envelope(tmp_path)
    source = next(record for record in envelope["files"] if record["path"] == "src/design.v")

    assert source["owner"] == "composite"
    assert [region["owner"] for region in source["regions"]] == [
        "trusted_builder",
        "model",
        "trusted_builder",
    ]
    assert source["regions"][0]["start_byte"] == 0
    assert source["regions"][-1]["end_byte"] == len(
        project.files["src/design.v"].encode("utf-8")
    )
    assert verify_project_envelope(
        project,
        envelope,
        event_ref_resolver=store.has_event_id,
    ) == []


def test_composite_verifier_rejects_forged_region_event_and_method_policy(tmp_path) -> None:
    project, store, envelope = _composite_envelope(tmp_path)

    forged_range = copy.deepcopy(envelope)
    source = next(record for record in forged_range["files"] if record["path"] == "src/design.v")
    source["regions"][1]["start_byte"] += 1
    forged_range["envelope_sha256"] = hashlib.sha256(
        (json.dumps(
            {key: value for key, value in forged_range.items() if key != "envelope_sha256"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )).encode("utf-8")
    ).hexdigest()
    assert any("ordered, contiguous" in error for error in verify_project_envelope(
        project, forged_range, event_ref_resolver=store.has_event_id
    ))

    forged_event = copy.deepcopy(envelope)
    source = next(record for record in forged_event["files"] if record["path"] == "src/design.v")
    source["regions"][1]["event_refs"] = ["event-" + "f" * 64]
    assert any("unresolved event" in error for error in verify_project_envelope(
        project, forged_event, event_ref_resolver=store.has_event_id
    ))

    forged_policy = copy.deepcopy(envelope)
    forged_policy["method_policy_sha256"] = "f" * 64
    assert any("registered method policy" in error for error in verify_project_envelope(
        project, forged_policy, event_ref_resolver=store.has_event_id
    ))
