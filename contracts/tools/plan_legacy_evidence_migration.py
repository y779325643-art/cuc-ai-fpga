"""Plan migration of active legacy tmp evidence without copying any files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
from typing import Any


PLAN_SCHEMA = "sr2fpga-legacy-active-evidence-migration-v1"
LEDGER_SCHEMA = "sr2fpga-task-evidence-v0.1"
CURATED_ROOT = PurePosixPath("reports/evidence/legacy-runs")


def _safe_relative_path(value: str, *, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not path.parts
        or path.is_absolute()
        or "." in path.parts
        or ".." in path.parts
    ):
        raise ValueError(f"unsafe {field}: {value!r}")
    return path


def _source_root(reference: PurePosixPath) -> PurePosixPath:
    if len(reference.parts) < 3 or reference.parts[0] != "tmp":
        raise ValueError(f"legacy evidence reference is outside tmp: {reference}")
    return PurePosixPath(*reference.parts[:2])


def _run_id_from_summary(reference: PurePosixPath) -> str | None:
    parts = reference.parts
    for index, part in enumerate(parts[:-2]):
        if part == "runs" and parts[index + 2] == "summary.json":
            return parts[index + 1]
    return None


def _reference_kind(reference: PurePosixPath) -> str:
    if reference.name == "oracle_mutations":
        return "subtree"
    return "file"


def build_plan(
    ledger: dict[str, Any],
    *,
    source_ledger: str,
) -> dict[str, Any]:
    if ledger.get("schema_version") != LEDGER_SCHEMA:
        raise ValueError("invalid task evidence ledger schema_version")

    source_ledger_path = _safe_relative_path(
        source_ledger,
        field="source_ledger",
    )
    families = ledger.get("task_families")
    if not isinstance(families, list):
        raise ValueError("task_families must be a list")

    reference_families: dict[str, set[str]] = {}
    occurrence_count = 0
    for family in families:
        if not isinstance(family, dict):
            raise ValueError("task family must be an object")
        family_id = str(family.get("family_id", "")).strip()
        if not family_id:
            raise ValueError("task family requires family_id")
        evidence_refs = family.get("evidence_refs", [])
        if not isinstance(evidence_refs, list):
            raise ValueError(f"evidence_refs must be a list: {family_id}")
        for raw_reference in evidence_refs:
            reference_text = str(raw_reference)
            if not reference_text.startswith("tmp/"):
                continue
            reference = _safe_relative_path(
                reference_text,
                field="evidence_reference",
            )
            _source_root(reference)
            occurrence_count += 1
            reference_families.setdefault(reference.as_posix(), set()).add(
                family_id
            )

    roots: dict[str, set[str]] = {}
    for reference_text in reference_families:
        reference = PurePosixPath(reference_text)
        root = _source_root(reference).as_posix()
        run_id = _run_id_from_summary(reference)
        if run_id is not None:
            roots.setdefault(root, set()).add(run_id)

    referenced_roots = {
        _source_root(PurePosixPath(reference)).as_posix()
        for reference in reference_families
    }
    for root in sorted(referenced_roots):
        run_ids = roots.get(root, set())
        if len(run_ids) != 1:
            raise ValueError(
                "legacy evidence source root requires exactly one run summary: "
                f"{root}"
            )

    run_groups: dict[str, dict[str, Any]] = {}
    destinations: set[str] = set()
    for reference_text in sorted(reference_families):
        reference = PurePosixPath(reference_text)
        root = _source_root(reference)
        run_id = next(iter(roots[root.as_posix()]))
        destination_root = CURATED_ROOT / run_id
        relative = reference.relative_to(root)
        destination = destination_root / relative
        if not destination.is_relative_to(CURATED_ROOT):
            raise ValueError(f"legacy evidence destination escapes root: {destination}")
        destination_text = destination.as_posix()
        if destination_text in destinations:
            raise ValueError(
                f"legacy evidence destination is not unique: {destination_text}"
            )
        destinations.add(destination_text)

        group = run_groups.setdefault(
            run_id,
            {
                "run_id": run_id,
                "source_root": root.as_posix(),
                "destination_root": destination_root.as_posix(),
                "references": [],
            },
        )
        if group["source_root"] != root.as_posix():
            raise ValueError(f"run_id is shared by multiple source roots: {run_id}")
        group["references"].append(
            {
                "source_reference": reference.as_posix(),
                "source_relative_path": relative.as_posix(),
                "destination_reference": destination_text,
                "reference_kind": _reference_kind(reference),
                "family_ids": sorted(reference_families[reference_text]),
                "migration_status": "requires_phase_a_backup",
            }
        )

    groups = []
    for run_id in sorted(run_groups):
        group = run_groups[run_id]
        group["references"] = sorted(
            group["references"],
            key=lambda record: record["source_reference"],
        )
        group["reference_count"] = len(group["references"])
        groups.append(group)

    unique_count = len(reference_families)
    planned_count = sum(group["reference_count"] for group in groups)
    if planned_count != unique_count:
        raise ValueError("legacy evidence plan does not cover every reference")

    return {
        "schema_version": PLAN_SCHEMA,
        "source_ledger": source_ledger_path.as_posix(),
        "curated_root": CURATED_ROOT.as_posix(),
        "status": "requires_phase_a_backup",
        "reference_occurrence_count": occurrence_count,
        "unique_reference_count": unique_count,
        "planned_reference_count": planned_count,
        "source_root_count": len(referenced_roots),
        "run_count": len(groups),
        "run_groups": groups,
    }


def write_plan(path: Path, plan: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
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
        "--ledger",
        type=Path,
        default=Path("docs/sr2fpga-task-evidence-v0.1.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "reports/reorganization/legacy-active-evidence-migration.json"
        ),
    )
    return parser.parse_args(argv)


def _within_root(root: Path, candidate: Path, *, field: str) -> Path:
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (root / candidate).resolve()
    )
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field} must stay inside the repository")
    return resolved


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = args.root.resolve()
        if not (root / ".git").exists():
            raise ValueError(f"repository .git entry is missing: {root}")
        ledger_path = _within_root(root, args.ledger, field="ledger")
        output_path = _within_root(root, args.output, field="output")
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        plan = build_plan(
            ledger,
            source_ledger=ledger_path.relative_to(root).as_posix(),
        )
        write_plan(output_path, plan)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        UnicodeDecodeError,
        ValueError,
    ) as error:
        print(error, file=sys.stderr)
        return 2

    print(output_path.relative_to(root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
