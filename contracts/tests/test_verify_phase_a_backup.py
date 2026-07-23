import hashlib
import json
from pathlib import Path

import pytest

from contracts.tools.verify_phase_a_backup import (
    verify_phase_a_backup,
    write_recheck,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _build_repository_and_backup(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    backup = tmp_path / "external-backup"
    (repository / ".git").mkdir(parents=True)
    workspace = backup / "workspace"
    restore = backup / "restore-test"
    workspace.mkdir(parents=True)
    restore.mkdir(parents=True)

    files = {
        "docs/status.json": b'{"status":"pass"}\n',
        "tmp/evidence.log": b"verified evidence\n",
    }
    records = []
    for relative, data in sorted(files.items()):
        workspace_path = workspace / Path(*relative.split("/"))
        workspace_path.parent.mkdir(parents=True, exist_ok=True)
        workspace_path.write_bytes(data)
        records.append(
            {
                "path": relative,
                "length": len(data),
                "sha256": _sha256(data),
            }
        )

    restore_sample = records[0]
    restore_path = restore / Path(*restore_sample["path"].split("/"))
    restore_path.parent.mkdir(parents=True, exist_ok=True)
    restore_path.write_bytes(files[restore_sample["path"]])

    manifest = {
        "schema_version": "sr2fpga-workspace-backup-v1",
        "file_count": len(records),
        "byte_count": sum(record["length"] for record in records),
        "files": records,
    }
    verification = {
        "schema_version": "sr2fpga-workspace-backup-verification-v1",
        "file_count": manifest["file_count"],
        "byte_count": manifest["byte_count"],
        "hash_failures": 0,
        "structured_parse_failures": 0,
        "restore_samples": [restore_sample["path"]],
        "status": "pass",
    }
    _write_json(backup / "manifest.json", manifest)
    _write_json(backup / "verification.json", verification)
    (backup / "checksums.sha256").write_text(
        "".join(
            f'{record["sha256"]}  {record["path"]}\n'
            for record in records
        ),
        encoding="utf-8",
    )
    for name in (
        "repository-state.json",
        "tracked-working-tree.patch",
        "staged-index.patch",
        "status.porcelain-v2.z",
        "worktrees.txt",
    ):
        (backup / name).write_bytes(b"phase-a\n")
    return repository, backup


def test_verified_external_backup_produces_pass_recheck(
    tmp_path: Path,
) -> None:
    repository, backup = _build_repository_and_backup(tmp_path)

    recheck = verify_phase_a_backup(
        repository,
        backup,
        checked_utc="2026-07-23T00:00:00+00:00",
    )

    assert recheck == {
        "schema_version": "sr2fpga-phase-b4-backup-recheck-v1",
        "checked_utc": "2026-07-23T00:00:00+00:00",
        "repository": str(repository.resolve()),
        "backup_root": str(backup.resolve()),
        "manifest_sha256": _sha256(
            (backup / "manifest.json").read_bytes()
        ),
        "file_count": 2,
        "byte_count": 36,
        "checksum_line_count": 2,
        "restore_sample_count": 1,
        "integrity_failure_count": 0,
        "status": "pass",
    }


def test_recheck_output_is_atomic_json(tmp_path: Path) -> None:
    repository, backup = _build_repository_and_backup(tmp_path)
    recheck = verify_phase_a_backup(repository, backup)
    output = repository / "artifacts" / "recheck.json"

    write_recheck(output, recheck)

    assert json.loads(output.read_text(encoding="utf-8")) == recheck
    assert list(output.parent.glob(f".{output.name}.*.tmp")) == []


def test_backup_inside_repository_is_rejected(tmp_path: Path) -> None:
    repository, external = _build_repository_and_backup(tmp_path)
    inside = repository / "backup"
    external.rename(inside)

    with pytest.raises(ValueError, match="inside the repository"):
        verify_phase_a_backup(repository, inside)


def test_workspace_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    repository, backup = _build_repository_and_backup(tmp_path)
    (backup / "workspace" / "tmp" / "evidence.log").write_bytes(b"changed\n")

    with pytest.raises(ValueError, match="length mismatch|sha256 mismatch"):
        verify_phase_a_backup(repository, backup)


def test_extra_workspace_file_is_rejected(tmp_path: Path) -> None:
    repository, backup = _build_repository_and_backup(tmp_path)
    (backup / "workspace" / "unexpected.txt").write_text(
        "unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="workspace path set mismatch"):
        verify_phase_a_backup(repository, backup)


def test_checksum_ledger_mismatch_is_rejected(tmp_path: Path) -> None:
    repository, backup = _build_repository_and_backup(tmp_path)
    (backup / "checksums.sha256").write_text(
        "0" * 64 + "  docs/status.json\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="checksum ledger"):
        verify_phase_a_backup(repository, backup)


@pytest.mark.parametrize(
    "unsafe_path",
    ("../escape.txt", "C:/escape.txt", r"folder\escape.txt"),
)
def test_unsafe_manifest_path_is_rejected(
    tmp_path: Path,
    unsafe_path: str,
) -> None:
    repository, backup = _build_repository_and_backup(tmp_path)
    manifest_path = backup / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = unsafe_path
    _write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="unsafe backup manifest path"):
        verify_phase_a_backup(repository, backup)


def test_invalid_verification_count_is_rejected(tmp_path: Path) -> None:
    repository, backup = _build_repository_and_backup(tmp_path)
    verification_path = backup / "verification.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    verification["file_count"] = None
    _write_json(verification_path, verification)

    with pytest.raises(ValueError, match="invalid verification file_count"):
        verify_phase_a_backup(repository, backup)
