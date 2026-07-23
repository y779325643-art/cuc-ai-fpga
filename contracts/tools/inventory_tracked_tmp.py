"""Inventory tracked tmp files without moving or deleting repository content."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from typing import Any


INVENTORY_SCHEMA = "sr2fpga-legacy-tmp-inventory-v1"
CLASSIFICATION_SCHEMA = "sr2fpga-legacy-tmp-classification-v1"
CURATED_ROOT = PurePosixPath("reports/evidence/legacy-runs")


def _git(root: Path, *arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=True,
    )
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8", errors="strict")


def resolve_repository_root(candidate: Path | None = None) -> Path:
    working_directory = (candidate or Path.cwd()).resolve()
    output = _git(working_directory, "rev-parse", "--show-toplevel")
    root = Path(str(output).strip()).resolve()
    if not (root / ".git").exists():
        raise ValueError(f"repository .git entry is missing: {root}")
    if candidate is not None and root != working_directory:
        raise ValueError(f"path is not the repository root: {working_directory}")
    return root


def tracked_tmp_entries(root: Path) -> list[dict[str, Any]]:
    raw = _git(root, "ls-files", "-s", "-z", "--", "tmp", binary=True)
    entries: list[dict[str, Any]] = []
    sizes: dict[str, int] = {}

    for raw_record in bytes(raw).split(b"\0"):
        if not raw_record:
            continue
        metadata, raw_path = raw_record.split(b"\t", 1)
        mode, object_id, stage = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8", errors="strict")
        if stage != "0":
            raise ValueError(f"unmerged tmp path cannot be inventoried: {path}")
        if object_id not in sizes:
            size_text = _git(root, "cat-file", "-s", object_id)
            sizes[object_id] = int(str(size_text).strip())
        entries.append(
            {
                "path": path,
                "git_mode": mode,
                "blob_oid": object_id,
                "blob_size": sizes[object_id],
            }
        )

    return sorted(entries, key=lambda record: record["path"])


def _safe_relative_path(value: str, *, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe {field}: {value!r}")
    return path


def load_classification_map(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != CLASSIFICATION_SCHEMA:
        raise ValueError("invalid tmp classification schema_version")
    mappings = payload.get("moved_to_curated_reports")
    if not isinstance(mappings, list):
        raise ValueError("moved_to_curated_reports must be a list")

    normalized: list[dict[str, Any]] = []
    selected_sources: set[str] = set()
    for mapping in mappings:
        if not isinstance(mapping, dict):
            raise ValueError("classification mapping must be an object")
        source_root = _safe_relative_path(
            str(mapping.get("source_root", "")),
            field="source_root",
        )
        destination_root = _safe_relative_path(
            str(mapping.get("destination_root", "")),
            field="destination_root",
        )
        include_paths = mapping.get("include_paths")
        if not include_paths or not isinstance(include_paths, list):
            raise ValueError("classification mapping requires include_paths")
        if not source_root.parts or source_root.parts[0] != "tmp":
            raise ValueError(f"classification source is outside tmp: {source_root}")
        if (
            destination_root == CURATED_ROOT
            or not destination_root.is_relative_to(CURATED_ROOT)
        ):
            raise ValueError(
                "classification destination must be a run directory below "
                "reports/evidence/legacy-runs/"
            )

        normalized_paths: list[str] = []
        for include_value in include_paths:
            relative = _safe_relative_path(
                str(include_value),
                field="include_path",
            )
            source = (source_root / relative).as_posix()
            if source in selected_sources:
                raise ValueError(f"tmp path classified more than once: {source}")
            selected_sources.add(source)
            normalized_paths.append(relative.as_posix())
        normalized.append(
            {
                "source_root": source_root.as_posix(),
                "destination_root": destination_root.as_posix(),
                "include_paths": sorted(normalized_paths),
            }
        )
    return sorted(normalized, key=lambda mapping: mapping["source_root"])


def build_inventory(
    root: Path,
    *,
    classification_path: Path | None,
    external_backup_manifest: str,
) -> dict[str, Any]:
    if not external_backup_manifest.strip():
        raise ValueError("external backup manifest name is required")
    if "/" in external_backup_manifest or "\\" in external_backup_manifest:
        raise ValueError("external backup manifest must be a file name")

    entries = tracked_tmp_entries(root)
    mappings = load_classification_map(classification_path)
    selected: dict[str, str] = {}
    tracked_paths = {entry["path"] for entry in entries}

    for mapping in mappings:
        source_root = PurePosixPath(mapping["source_root"])
        destination_root = PurePosixPath(mapping["destination_root"])
        for relative_text in mapping["include_paths"]:
            relative = PurePosixPath(relative_text)
            source = (source_root / relative).as_posix()
            if source not in tracked_paths:
                raise ValueError(
                    f"classified tmp path is not tracked: {source}"
                )
            selected[source] = (destination_root / relative).as_posix()

    records: list[dict[str, Any]] = []
    for entry in entries:
        record = dict(entry)
        destination = selected.get(entry["path"])
        if destination is None:
            record.update(
                {
                    "disposition": "external_backup_only",
                    "external_backup_manifest": external_backup_manifest,
                }
            )
        else:
            record.update(
                {
                    "disposition": "moved_to_curated_reports",
                    "destination": destination,
                }
            )
        records.append(record)

    moved_count = len(selected)
    return {
        "schema_version": INVENTORY_SCHEMA,
        "tracked_root": "tmp",
        "classification_map": (
            classification_path.resolve().relative_to(root).as_posix()
            if classification_path is not None
            else None
        ),
        "external_backup_manifest": external_backup_manifest,
        "tracked_path_count": len(records),
        "total_blob_bytes": sum(record["blob_size"] for record in records),
        "disposition_counts": {
            "moved_to_curated_reports": moved_count,
            "external_backup_only": len(records) - moved_count,
        },
        "records": records,
    }


def write_inventory(path: Path, inventory: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(inventory, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n"
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
    parser.add_argument("--root", type=Path)
    parser.add_argument("--classification-map", type=Path)
    parser.add_argument(
        "--external-backup-manifest",
        default="manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/reorganization/legacy-tmp-inventory.json"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_repository_root(args.root)
        classification_path = (
            (root / args.classification_map).resolve()
            if args.classification_map is not None
            and not args.classification_map.is_absolute()
            else args.classification_map
        )
        output_path = (
            (root / args.output).resolve()
            if not args.output.is_absolute()
            else args.output.resolve()
        )
        if not output_path.is_relative_to(root):
            raise ValueError("inventory output must stay inside the repository")
        if (
            classification_path is not None
            and not classification_path.is_relative_to(root)
        ):
            raise ValueError(
                "classification map must stay inside the repository"
            )
        inventory = build_inventory(
            root,
            classification_path=classification_path,
            external_backup_manifest=args.external_backup_manifest,
        )
        write_inventory(output_path, inventory)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        subprocess.CalledProcessError,
        UnicodeDecodeError,
        ValueError,
    ) as error:
        print(error, file=sys.stderr)
        return 2

    print(output_path.relative_to(root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
