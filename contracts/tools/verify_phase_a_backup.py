"""Reverify an explicitly supplied Phase A external workspace backup."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any


MANIFEST_SCHEMA = "sr2fpga-workspace-backup-v1"
VERIFICATION_SCHEMA = "sr2fpga-workspace-backup-verification-v1"
RECHECK_SCHEMA = "sr2fpga-phase-b4-backup-recheck-v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_FILES = (
    "repository-state.json",
    "tracked-working-tree.patch",
    "staged-index.patch",
    "status.porcelain-v2.z",
    "worktrees.txt",
    "manifest.json",
    "verification.json",
    "checksums.sha256",
)
REQUIRED_DIRECTORIES = ("workspace", "restore-test")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON document must be an object: {path.name}")
    return payload


def _safe_member(root: Path, relative_text: str) -> Path:
    relative = PurePosixPath(relative_text)
    if (
        not relative.parts
        or relative.is_absolute()
        or "\\" in relative_text
        or re.match(r"^[A-Za-z]:", relative_text)
        or "." in relative.parts
        or ".." in relative.parts
    ):
        raise ValueError(f"unsafe backup manifest path: {relative_text!r}")
    candidate = (root / Path(*relative.parts)).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"backup manifest path escapes its root: {relative_text}")
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    raw_records = manifest.get("files")
    if not isinstance(raw_records, list):
        raise ValueError("backup manifest files must be a list")

    records: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            raise ValueError("backup manifest file record must be an object")
        path = str(raw_record.get("path", ""))
        _safe_member(Path.cwd().resolve(), path)
        if path in seen_paths:
            raise ValueError(f"duplicate backup manifest path: {path}")
        seen_paths.add(path)
        try:
            length = int(raw_record["length"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid backup length: {path}") from error
        sha256 = str(raw_record.get("sha256", "")).lower()
        if length < 0 or SHA256_PATTERN.fullmatch(sha256) is None:
            raise ValueError(f"invalid backup record: {path}")
        records.append({"path": path, "length": length, "sha256": sha256})

    if [record["path"] for record in records] != sorted(
        record["path"] for record in records
    ):
        raise ValueError("backup manifest records are not sorted by path")
    return records


def _assert_external_backup(repository: Path, backup: Path) -> None:
    if backup == repository or backup.is_relative_to(repository):
        raise ValueError("external backup root resolves inside the repository")


def _verify_required_layout(backup: Path) -> None:
    for relative in REQUIRED_FILES:
        if not (backup / relative).is_file():
            raise FileNotFoundError(f"missing Phase A backup file: {relative}")
    for relative in REQUIRED_DIRECTORIES:
        if not (backup / relative).is_dir():
            raise FileNotFoundError(
                f"missing Phase A backup directory: {relative}"
            )


def _verify_checksum_ledger(
    backup: Path,
    records: list[dict[str, Any]],
) -> int:
    lines = (backup / "checksums.sha256").read_text(
        encoding="utf-8"
    ).splitlines()
    expected = [
        f'{record["sha256"]}  {record["path"]}' for record in records
    ]
    if lines != expected:
        raise ValueError("backup checksum ledger does not match manifest records")
    return len(lines)


def _workspace_files(workspace: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(workspace):
            raise ValueError(f"workspace file escapes backup root: {path}")
        relative = resolved.relative_to(workspace).as_posix()
        files[relative] = resolved
    return files


def _verify_workspace(
    workspace: Path,
    records: list[dict[str, Any]],
) -> None:
    actual_files = _workspace_files(workspace)
    expected_paths = {record["path"] for record in records}
    actual_paths = set(actual_files)
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)
        raise ValueError(
            "backup workspace path set mismatch: "
            f"missing={missing[:5]}, extra={extra[:5]}"
        )

    for record in records:
        path = actual_files[record["path"]]
        if path.stat().st_size != record["length"]:
            raise ValueError(f'backup length mismatch: {record["path"]}')
        if _sha256(path) != record["sha256"]:
            raise ValueError(f'backup sha256 mismatch: {record["path"]}')


def _verify_restore_samples(
    restore_root: Path,
    verification: dict[str, Any],
    records: list[dict[str, Any]],
) -> int:
    samples = verification.get("restore_samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("verification contains no restore samples")
    record_map = {record["path"]: record for record in records}
    if len(record_map) != len(records):
        raise ValueError("backup manifest paths are not unique")

    for raw_sample in samples:
        sample = str(raw_sample)
        record = record_map.get(sample)
        if record is None:
            raise ValueError(f"restore sample is not in manifest: {sample}")
        restored = _safe_member(restore_root, sample)
        if not restored.is_file():
            raise FileNotFoundError(f"missing restore sample: {sample}")
        if restored.stat().st_size != record["length"]:
            raise ValueError(f"restore sample length mismatch: {sample}")
        if _sha256(restored) != record["sha256"]:
            raise ValueError(f"restore sample sha256 mismatch: {sample}")
    return len(samples)


def verify_phase_a_backup(
    repository: Path,
    backup_root: Path,
    *,
    checked_utc: str | None = None,
) -> dict[str, Any]:
    repository = repository.resolve()
    backup = backup_root.resolve()
    if not (repository / ".git").exists():
        raise ValueError(f"repository .git entry is missing: {repository}")
    if not backup.is_dir():
        raise FileNotFoundError(f"external backup root is missing: {backup}")
    _assert_external_backup(repository, backup)
    _verify_required_layout(backup)

    manifest = _load_json(backup / "manifest.json")
    verification = _load_json(backup / "verification.json")
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise ValueError("unexpected backup manifest schema")
    if verification.get("schema_version") != VERIFICATION_SCHEMA:
        raise ValueError("unexpected backup verification schema")
    if verification.get("status") != "pass":
        raise ValueError("Phase A verification status is not pass")
    if int(verification.get("hash_failures", -1)) != 0:
        raise ValueError("Phase A verification reports hash failures")
    if int(verification.get("structured_parse_failures", -1)) != 0:
        raise ValueError("Phase A verification reports parse failures")

    records = _normalized_records(manifest)
    manifest_count = int(manifest.get("file_count", -1))
    manifest_bytes = int(manifest.get("byte_count", -1))
    if manifest_count != len(records):
        raise ValueError("backup manifest record count mismatch")
    if manifest_bytes != sum(record["length"] for record in records):
        raise ValueError("backup manifest byte count mismatch")
    if int(verification.get("file_count", -1)) != manifest_count:
        raise ValueError("manifest and verification file counts disagree")
    if int(verification.get("byte_count", -1)) != manifest_bytes:
        raise ValueError("manifest and verification byte counts disagree")

    checksum_line_count = _verify_checksum_ledger(backup, records)
    workspace = (backup / "workspace").resolve()
    _verify_workspace(workspace, records)
    restore_sample_count = _verify_restore_samples(
        (backup / "restore-test").resolve(),
        verification,
        records,
    )

    return {
        "schema_version": RECHECK_SCHEMA,
        "checked_utc": checked_utc
        or datetime.now(timezone.utc).isoformat(),
        "repository": str(repository),
        "backup_root": str(backup),
        "file_count": manifest_count,
        "byte_count": manifest_bytes,
        "checksum_line_count": checksum_line_count,
        "restore_sample_count": restore_sample_count,
        "integrity_failure_count": 0,
        "status": "pass",
    }


def write_recheck(path: Path, recheck: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(recheck, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(encoded)
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _output_path(repository: Path, candidate: Path) -> Path:
    output = (
        candidate.resolve()
        if candidate.is_absolute()
        else (repository / candidate).resolve()
    )
    allowed_root = (
        repository / "artifacts" / "reorganization" / "phase-b4"
    ).resolve()
    if not output.is_relative_to(allowed_root):
        raise ValueError(
            "backup recheck output must stay under "
            "artifacts/reorganization/phase-b4/"
        )
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--backup-root",
        type=Path,
        default=(
            Path(os.environ["SR2FPGA_PHASE_A_BACKUP_ROOT"])
            if os.environ.get("SR2FPGA_PHASE_A_BACKUP_ROOT")
            else None
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/reorganization/phase-b4/backup-recheck.json"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.backup_root is None:
            raise ValueError(
                "Phase A backup root is required via --backup-root or "
                "SR2FPGA_PHASE_A_BACKUP_ROOT"
            )
        repository = args.root.resolve()
        output = _output_path(repository, args.output)
        recheck = verify_phase_a_backup(repository, args.backup_root)
        write_recheck(output, recheck)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        UnicodeDecodeError,
        ValueError,
    ) as error:
        print(error, file=sys.stderr)
        return 2

    print(output.relative_to(repository).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
