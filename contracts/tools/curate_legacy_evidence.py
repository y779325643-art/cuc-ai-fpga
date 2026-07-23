"""Preview or copy verified legacy evidence into stable report paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from typing import Any


CURATION_SCHEMA = "sr2fpga-legacy-evidence-curation-v1"
PLAN_SCHEMA = "sr2fpga-legacy-active-evidence-migration-v1"
RECHECK_SCHEMA = "sr2fpga-phase-b4-backup-recheck-v1"
MANIFEST_SCHEMA = "sr2fpga-workspace-backup-v1"
CURATED_ROOT = PurePosixPath("reports/evidence/legacy-runs")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SECRET_PATTERNS = (
    re.compile(rb"(?<![A-Za-z0-9_])sk-[A-Za-z0-9]{20,}"),
    re.compile(
        rb"(?:ANTHROPIC|OPENAI)_API_KEY\s*[:=]\s*[\"']?"
        rb"[A-Za-z0-9_.-]{20,}",
        re.IGNORECASE,
    ),
)
PRIVATE_PATH_PATTERNS = (
    re.compile(rb"(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?![<\[])"),
    re.compile(rb"/mnt/[A-Za-z]/(?:Users/)?[^/\s`\"'<>|]+/"),
    re.compile(rb"/home/[^/\s`\"'<>|]+/"),
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: str, *, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not path.parts
        or path.is_absolute()
        or "\\" in value
        or re.match(r"^[A-Za-z]:", value)
        or "." in path.parts
        or ".." in path.parts
    ):
        raise ValueError(f"unsafe {field}: {value!r}")
    return path


def _repository_path(
    repository: Path,
    value: str,
    *,
    field: str,
) -> Path:
    relative = _safe_relative(value, field=field)
    candidate = (repository / Path(*relative.parts)).resolve()
    if not candidate.is_relative_to(repository):
        raise ValueError(f"{field} escapes repository: {value}")
    return candidate


def _backup_path(
    backup_workspace: Path,
    value: str,
) -> Path:
    relative = _safe_relative(value, field="backup_path")
    candidate = (backup_workspace / Path(*relative.parts)).resolve()
    if not candidate.is_relative_to(backup_workspace):
        raise ValueError(f"backup path escapes workspace: {value}")
    return candidate


def _manifest_records(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise ValueError("unexpected backup manifest schema")
    raw_records = manifest.get("files")
    if not isinstance(raw_records, list):
        raise ValueError("backup manifest files must be a list")

    records: dict[str, dict[str, Any]] = {}
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            raise ValueError("backup manifest record must be an object")
        path = _safe_relative(
            str(raw_record.get("path", "")),
            field="manifest_path",
        ).as_posix()
        if path in records:
            raise ValueError(f"duplicate backup manifest path: {path}")
        try:
            length = int(raw_record["length"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid backup manifest length: {path}") from error
        digest = str(raw_record.get("sha256", "")).lower()
        if length < 0 or SHA256_PATTERN.fullmatch(digest) is None:
            raise ValueError(f"invalid backup manifest record: {path}")
        records[path] = {
            "path": path,
            "length": length,
            "sha256": digest,
        }
    return records


def _validate_recheck(
    repository: Path,
    backup: Path,
    recheck_path: Path,
) -> dict[str, Any]:
    recheck = _load_json(recheck_path)
    if recheck.get("schema_version") != RECHECK_SCHEMA:
        raise ValueError("unexpected backup recheck schema")
    if recheck.get("status") != "pass":
        raise ValueError("Phase B4 backup recheck status is not pass")
    if Path(str(recheck.get("repository", ""))).resolve() != repository:
        raise ValueError("backup recheck belongs to another repository")
    if Path(str(recheck.get("backup_root", ""))).resolve() != backup:
        raise ValueError("backup recheck belongs to another backup root")
    if int(recheck.get("integrity_failure_count", -1)) != 0:
        raise ValueError("backup recheck reports integrity failures")
    return recheck


def _expand_reference(
    records: dict[str, dict[str, Any]],
    source_reference: str,
    reference_kind: str,
) -> list[dict[str, Any]]:
    if reference_kind == "file":
        record = records.get(source_reference)
        if record is None:
            raise ValueError(
                f"planned evidence file is absent from backup: {source_reference}"
            )
        return [record]
    if reference_kind == "subtree":
        prefix = source_reference.rstrip("/") + "/"
        selected = [
            record
            for path, record in sorted(records.items())
            if path.startswith(prefix)
        ]
        if not selected:
            raise ValueError(
                f"planned evidence subtree is absent from backup: "
                f"{source_reference}"
            )
        return selected
    raise ValueError(f"unsupported evidence reference kind: {reference_kind}")


def _destination_for_record(
    source_reference: PurePosixPath,
    destination_reference: PurePosixPath,
    reference_kind: str,
    record_path: PurePosixPath,
) -> PurePosixPath:
    if reference_kind == "file":
        if record_path != source_reference:
            raise ValueError("file evidence expansion selected another path")
        return destination_reference
    relative = record_path.relative_to(source_reference)
    return destination_reference / relative


def _scan_content(path: Path) -> tuple[bool, bool]:
    content = path.read_bytes()
    has_secret = any(pattern.search(content) for pattern in SECRET_PATTERNS)
    has_private_path = any(
        pattern.search(content) for pattern in PRIVATE_PATH_PATTERNS
    )
    return has_secret, has_private_path


def build_curation_preview(
    repository: Path,
    backup_root: Path,
    *,
    plan_path: Path,
    recheck_path: Path,
) -> dict[str, Any]:
    repository = repository.resolve()
    backup = backup_root.resolve()
    plan_path = plan_path.resolve()
    recheck_path = recheck_path.resolve()
    if not (repository / ".git").exists():
        raise ValueError(f"repository .git entry is missing: {repository}")
    if not backup.is_dir():
        raise FileNotFoundError(f"backup root is missing: {backup}")
    if backup == repository or backup.is_relative_to(repository):
        raise ValueError("backup root resolves inside repository")
    if not plan_path.is_relative_to(repository):
        raise ValueError("migration plan must stay inside repository")
    if not recheck_path.is_relative_to(repository):
        raise ValueError("backup recheck must stay inside repository")
    _validate_recheck(repository, backup, recheck_path)

    plan = _load_json(plan_path)
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("unexpected legacy evidence migration schema")
    run_groups = plan.get("run_groups")
    if not isinstance(run_groups, list):
        raise ValueError("legacy evidence run_groups must be a list")

    manifest_path = backup / "manifest.json"
    manifest = _load_json(manifest_path)
    records = _manifest_records(manifest)
    workspace = (backup / "workspace").resolve()
    if not workspace.is_relative_to(backup):
        raise ValueError("backup workspace escapes backup root")

    selected_files: dict[str, dict[str, Any]] = {}
    destination_sources: dict[str, str] = {}
    secret_paths: set[str] = set()
    private_paths: set[str] = set()
    reference_count = 0

    for group in run_groups:
        if not isinstance(group, dict):
            raise ValueError("legacy evidence run group must be an object")
        run_id = str(group.get("run_id", ""))
        if (
            not run_id
            or PurePosixPath(run_id).name != run_id
            or run_id in {".", ".."}
        ):
            raise ValueError(f"unsafe legacy evidence run_id: {run_id!r}")
        destination_root = _safe_relative(
            str(group.get("destination_root", "")),
            field="destination_root",
        )
        if destination_root != CURATED_ROOT / run_id:
            raise ValueError(f"unexpected destination root for run: {run_id}")
        references = group.get("references")
        if not isinstance(references, list):
            raise ValueError(f"references must be a list: {run_id}")

        for reference in references:
            if not isinstance(reference, dict):
                raise ValueError("legacy evidence reference must be an object")
            source_reference = _safe_relative(
                str(reference.get("source_reference", "")),
                field="source_reference",
            )
            if source_reference.parts[0] != "tmp":
                raise ValueError(
                    f"evidence source is outside tmp: {source_reference}"
                )
            destination_reference = _safe_relative(
                str(reference.get("destination_reference", "")),
                field="destination_reference",
            )
            if not destination_reference.is_relative_to(destination_root):
                raise ValueError(
                    f"evidence destination escapes run root: "
                    f"{destination_reference}"
                )
            reference_kind = str(reference.get("reference_kind", ""))
            expanded = _expand_reference(
                records,
                source_reference.as_posix(),
                reference_kind,
            )
            reference_count += 1

            for record in expanded:
                record_path = PurePosixPath(record["path"])
                destination = _destination_for_record(
                    source_reference,
                    destination_reference,
                    reference_kind,
                    record_path,
                )
                destination_text = destination.as_posix()
                prior_source = destination_sources.get(destination_text)
                if prior_source is not None and prior_source != record["path"]:
                    raise ValueError(
                        f"multiple sources map to evidence destination: "
                        f"{destination_text}"
                    )
                destination_sources[destination_text] = record["path"]
                prior_record = selected_files.get(record["path"])
                if (
                    prior_record is not None
                    and prior_record["destination_path"] != destination_text
                ):
                    raise ValueError(
                        f"evidence source maps to multiple destinations: "
                        f"{record['path']}"
                    )

                source = _backup_path(workspace, record["path"])
                if not source.is_file():
                    raise FileNotFoundError(
                        f'backup evidence file is missing: {record["path"]}'
                    )
                if source.stat().st_size != record["length"]:
                    raise ValueError(
                        f'backup evidence length mismatch: {record["path"]}'
                    )
                if _sha256(source) != record["sha256"]:
                    raise ValueError(
                        f'backup evidence sha256 mismatch: {record["path"]}'
                    )
                has_secret, has_private_path = _scan_content(source)
                if has_secret:
                    secret_paths.add(record["path"])
                if has_private_path:
                    private_paths.add(record["path"])

                selected_files[record["path"]] = {
                    "run_id": run_id,
                    "source_path": record["path"],
                    "destination_path": destination_text,
                    "length": record["length"],
                    "sha256": record["sha256"],
                }

    expected_references = int(plan.get("planned_reference_count", -1))
    if reference_count != expected_references:
        raise ValueError(
            "migration plan reference count changed during curation preview"
        )

    blocked = bool(secret_paths or private_paths)
    files = sorted(
        selected_files.values(),
        key=lambda record: record["destination_path"],
    )
    return {
        "schema_version": CURATION_SCHEMA,
        "mode": "preview",
        "status": "blocked_review" if blocked else "ready",
        "source_plan": plan_path.relative_to(repository).as_posix(),
        "source_plan_sha256": _sha256(plan_path),
        "source_backup_manifest_sha256": _sha256(manifest_path),
        "backup_recheck": recheck_path.relative_to(repository).as_posix(),
        "run_count": len(run_groups),
        "reference_count": reference_count,
        "selected_file_count": len(files),
        "selected_file_bytes": sum(record["length"] for record in files),
        "blocked_secret_paths": sorted(secret_paths),
        "private_path_review_paths": sorted(private_paths),
        "files": files,
    }


def apply_curation(
    repository: Path,
    backup_root: Path,
    preview: dict[str, Any],
) -> dict[str, Any]:
    repository = repository.resolve()
    backup = backup_root.resolve()
    if preview.get("schema_version") != CURATION_SCHEMA:
        raise ValueError("unexpected curation preview schema")
    if preview.get("status") != "ready":
        raise ValueError("curation preview is not ready to apply")

    workspace = (backup / "workspace").resolve()
    operations: list[tuple[dict[str, Any], Path, Path, bool]] = []
    raw_files = preview.get("files")
    if not isinstance(raw_files, list):
        raise ValueError("curation preview files must be a list")
    for record in raw_files:
        if not isinstance(record, dict):
            raise ValueError("curation file record must be an object")
        source_relative = _safe_relative(
            str(record.get("source_path", "")),
            field="source_path",
        )
        if source_relative.parts[0] != "tmp":
            raise ValueError(f"curation source is outside tmp: {source_relative}")
        destination_relative = _safe_relative(
            str(record.get("destination_path", "")),
            field="destination_path",
        )
        if not destination_relative.is_relative_to(CURATED_ROOT):
            raise ValueError(
                f"curation destination escapes curated root: "
                f"{destination_relative}"
            )
        source = _backup_path(workspace, source_relative.as_posix())
        destination = _repository_path(
            repository,
            destination_relative.as_posix(),
            field="destination_path",
        )
        expected_hash = str(record.get("sha256", ""))
        expected_length = int(record.get("length", -1))
        if not source.is_file():
            raise FileNotFoundError(f"curation source is missing: {source}")
        if source.stat().st_size != expected_length:
            raise ValueError(f"curation source length changed: {source}")
        if _sha256(source) != expected_hash:
            raise ValueError(f"curation source hash changed: {source}")

        reuse = destination.exists()
        if reuse:
            if not destination.is_file():
                raise ValueError(
                    f"curation destination is not a file: {destination}"
                )
            if (
                destination.stat().st_size != expected_length
                or _sha256(destination) != expected_hash
            ):
                raise ValueError(
                    f"curation destination conflicts: {destination}"
                )
        operations.append((record, source, destination, reuse))

    copied = 0
    reused = 0
    for record, source, destination, reuse in operations:
        if reuse:
            reused += 1
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
            shutil.copyfile(source, temporary_path)
            if _sha256(temporary_path) != record["sha256"]:
                raise ValueError(
                    f"curation copy hash mismatch: {record['destination_path']}"
                )
            temporary_path.replace(destination)
            copied += 1
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    result = dict(preview)
    result.update(
        {
            "mode": "applied",
            "status": "pass",
            "copied_file_count": copied,
            "reused_file_count": reused,
        }
    )
    return result


def write_curation(path: Path, curation: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(curation, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
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
        "--plan",
        type=Path,
        default=Path(
            "reports/reorganization/legacy-active-evidence-migration.json"
        ),
    )
    parser.add_argument(
        "--recheck",
        type=Path,
        default=Path(
            "artifacts/reorganization/phase-b4/backup-recheck.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/reorganization/phase-b4/"
            "legacy-evidence-curation-preview.json"
        ),
    )
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def _inside_repository(repository: Path, candidate: Path, *, field: str) -> Path:
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (repository / candidate).resolve()
    )
    if not resolved.is_relative_to(repository):
        raise ValueError(f"{field} must stay inside repository")
    return resolved


def _output_path(
    repository: Path,
    candidate: Path,
    *,
    apply: bool,
) -> Path:
    output = _inside_repository(repository, candidate, field="output")
    allowed = (
        repository / "reports" / "reorganization"
        if apply
        else repository / "artifacts" / "reorganization" / "phase-b4"
    ).resolve()
    if not output.is_relative_to(allowed):
        mode = "applied" if apply else "preview"
        raise ValueError(
            f"{mode} curation output must stay under "
            f"{allowed.relative_to(repository).as_posix()}/"
        )
    return output


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.backup_root is None:
            raise ValueError(
                "Phase A backup root is required via --backup-root or "
                "SR2FPGA_PHASE_A_BACKUP_ROOT"
            )
        repository = args.root.resolve()
        plan_path = _inside_repository(repository, args.plan, field="plan")
        recheck_path = _inside_repository(
            repository,
            args.recheck,
            field="recheck",
        )
        output_path = _output_path(
            repository,
            args.output,
            apply=args.apply,
        )
        preview = build_curation_preview(
            repository,
            args.backup_root,
            plan_path=plan_path,
            recheck_path=recheck_path,
        )
        result = (
            apply_curation(repository, args.backup_root, preview)
            if args.apply
            else preview
        )
        write_curation(output_path, result)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
    ) as error:
        print(error, file=sys.stderr)
        return 2

    print(output_path.relative_to(repository).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
