import hashlib
import json
from pathlib import Path

import pytest

from contracts.tools.curate_legacy_evidence import (
    apply_curation,
    build_curation_preview,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repository = tmp_path / "repository"
    backup = tmp_path / "external-backup"
    (repository / ".git").mkdir(parents=True)
    workspace = backup / "workspace"
    workspace.mkdir(parents=True)

    files = {
        "tmp/source/runs/run-1/summary.json": b'{"status":"pass"}\n',
        "tmp/source/dataset/sample/oracle_mutations/first.json": (
            b'{"mutation":"first"}\n'
        ),
        "tmp/source/dataset/sample/oracle_mutations/second.log": b"killed\n",
        "tmp/source/unrelated.txt": b"not selected\n",
    }
    records = []
    for relative, content in sorted(files.items()):
        path = workspace / Path(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        records.append(
            {
                "path": relative,
                "length": len(content),
                "sha256": _sha256(content),
            }
        )
    _write_json(
        backup / "manifest.json",
        {
            "schema_version": "sr2fpga-workspace-backup-v1",
            "files": records,
        },
    )

    plan_path = repository / "reports" / "reorganization" / "plan.json"
    _write_json(
        plan_path,
        {
            "schema_version": (
                "sr2fpga-legacy-active-evidence-migration-v1"
            ),
            "planned_reference_count": 2,
            "run_groups": [
                {
                    "run_id": "run-1",
                    "destination_root": (
                        "reports/evidence/legacy-runs/run-1"
                    ),
                    "references": [
                        {
                            "source_reference": (
                                "tmp/source/runs/run-1/summary.json"
                            ),
                            "destination_reference": (
                                "reports/evidence/legacy-runs/run-1/"
                                "runs/run-1/summary.json"
                            ),
                            "reference_kind": "file",
                        },
                        {
                            "source_reference": (
                                "tmp/source/dataset/sample/oracle_mutations"
                            ),
                            "destination_reference": (
                                "reports/evidence/legacy-runs/run-1/"
                                "dataset/sample/oracle_mutations"
                            ),
                            "reference_kind": "subtree",
                        },
                    ],
                }
            ],
        },
    )
    recheck_path = (
        repository
        / "artifacts"
        / "reorganization"
        / "phase-b4"
        / "backup-recheck.json"
    )
    _write_json(
        recheck_path,
        {
            "schema_version": "sr2fpga-phase-b4-backup-recheck-v1",
            "repository": str(repository.resolve()),
            "backup_root": str(backup.resolve()),
            "integrity_failure_count": 0,
            "status": "pass",
        },
    )
    return repository, backup, plan_path, recheck_path


def test_preview_expands_only_planned_files(tmp_path: Path) -> None:
    repository, backup, plan_path, recheck_path = _fixture(tmp_path)

    preview = build_curation_preview(
        repository,
        backup,
        plan_path=plan_path,
        recheck_path=recheck_path,
    )

    assert preview["status"] == "ready"
    assert preview["reference_count"] == 2
    assert preview["selected_file_count"] == 3
    assert preview["blocked_secret_paths"] == []
    assert preview["private_path_review_paths"] == []
    assert all(
        "unrelated.txt" not in record["source_path"]
        for record in preview["files"]
    )
    assert {
        record["destination_path"] for record in preview["files"]
    } == {
        "reports/evidence/legacy-runs/run-1/"
        "runs/run-1/summary.json",
        "reports/evidence/legacy-runs/run-1/"
        "dataset/sample/oracle_mutations/first.json",
        "reports/evidence/legacy-runs/run-1/"
        "dataset/sample/oracle_mutations/second.log",
    }
    assert not (repository / "reports" / "evidence").exists()


def test_apply_copies_exact_files_and_is_idempotent(tmp_path: Path) -> None:
    repository, backup, plan_path, recheck_path = _fixture(tmp_path)
    preview = build_curation_preview(
        repository,
        backup,
        plan_path=plan_path,
        recheck_path=recheck_path,
    )

    first = apply_curation(repository, backup, preview)
    second = apply_curation(repository, backup, preview)

    assert first["status"] == "pass"
    assert first["copied_file_count"] == 3
    assert first["reused_file_count"] == 0
    assert second["copied_file_count"] == 0
    assert second["reused_file_count"] == 3
    for record in preview["files"]:
        destination = repository / Path(*record["destination_path"].split("/"))
        assert destination.is_file()
        assert _sha256(destination.read_bytes()) == record["sha256"]


def test_recheck_for_another_backup_is_rejected(tmp_path: Path) -> None:
    repository, backup, plan_path, recheck_path = _fixture(tmp_path)
    recheck = json.loads(recheck_path.read_text(encoding="utf-8"))
    recheck["backup_root"] = str((tmp_path / "other").resolve())
    _write_json(recheck_path, recheck)

    with pytest.raises(ValueError, match="another backup root"):
        build_curation_preview(
            repository,
            backup,
            plan_path=plan_path,
            recheck_path=recheck_path,
        )


def test_secret_content_blocks_apply(tmp_path: Path) -> None:
    repository, backup, plan_path, recheck_path = _fixture(tmp_path)
    summary = backup / "workspace" / "tmp" / "source" / "runs" / "run-1"
    summary_file = summary / "summary.json"
    secret_content = b'{"key":"sk-123456789012345678901234"}\n'
    summary_file.write_bytes(secret_content)
    manifest_path = backup / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["files"]:
        if record["path"].endswith("/summary.json"):
            record["length"] = len(secret_content)
            record["sha256"] = _sha256(secret_content)
    _write_json(manifest_path, manifest)

    preview = build_curation_preview(
        repository,
        backup,
        plan_path=plan_path,
        recheck_path=recheck_path,
    )

    assert preview["status"] == "blocked_review"
    assert preview["blocked_secret_paths"] == [
        "tmp/source/runs/run-1/summary.json"
    ]
    with pytest.raises(ValueError, match="not ready"):
        apply_curation(repository, backup, preview)


def test_private_absolute_path_requires_review(tmp_path: Path) -> None:
    repository, backup, plan_path, recheck_path = _fixture(tmp_path)
    summary_file = (
        backup
        / "workspace"
        / "tmp"
        / "source"
        / "runs"
        / "run-1"
        / "summary.json"
    )
    private_content = b'{"report":"D:/Users/private/report.json"}\n'
    summary_file.write_bytes(private_content)
    manifest_path = backup / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["files"]:
        if record["path"].endswith("/summary.json"):
            record["length"] = len(private_content)
            record["sha256"] = _sha256(private_content)
    _write_json(manifest_path, manifest)

    preview = build_curation_preview(
        repository,
        backup,
        plan_path=plan_path,
        recheck_path=recheck_path,
    )

    assert preview["status"] == "blocked_review"
    assert preview["private_path_review_paths"] == [
        "tmp/source/runs/run-1/summary.json"
    ]


def test_conflicting_destination_is_rejected_before_copy(
    tmp_path: Path,
) -> None:
    repository, backup, plan_path, recheck_path = _fixture(tmp_path)
    preview = build_curation_preview(
        repository,
        backup,
        plan_path=plan_path,
        recheck_path=recheck_path,
    )
    destination = repository / Path(
        *preview["files"][0]["destination_path"].split("/")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("conflict\n", encoding="utf-8")

    with pytest.raises(ValueError, match="destination conflicts"):
        apply_curation(repository, backup, preview)


def test_apply_rejects_destination_outside_curated_root(
    tmp_path: Path,
) -> None:
    repository, backup, plan_path, recheck_path = _fixture(tmp_path)
    preview = build_curation_preview(
        repository,
        backup,
        plan_path=plan_path,
        recheck_path=recheck_path,
    )
    preview["files"][0]["destination_path"] = "agent/escaped.json"

    with pytest.raises(ValueError, match="escapes curated root"):
        apply_curation(repository, backup, preview)
