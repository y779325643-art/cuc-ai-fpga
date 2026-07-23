"""Promote regenerated evidence into stable, sanitized repository paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any


PROMOTION_SCHEMA = "sr2fpga-regenerated-evidence-promotion-v1"
PLAN_SCHEMA = "sr2fpga-legacy-active-evidence-migration-v1"
SOURCE_SCHEMA = "sr2fpga-regenerated-evidence-sources-v1"
CURATED_ROOT = PurePosixPath("reports/evidence/legacy-runs")
RUN_FILES = (
    "baseline_report.md",
    "config.json",
    "events.jsonl",
    "measurement_freeze.json",
    "run_state.json",
    "summary.json",
)
SAMPLE_ROOT_FILES = (
    "metadata.json",
    "platform_profile.json",
    "requirement.txt",
)
GENERATED_PROJECT_DIRECTORIES = (
    "constraints",
    "reports",
    "rtl",
    "sim",
)
OPENXC7_EVIDENCE_FILES = (
    "openxc7_clock.xdc",
    "openxc7_nextpnr.log",
    "openxc7_report.json",
    "openxc7_yosys.log",
    "openxc7_yosys.ys",
)
ATTEMPT_EVAL_FILES = frozenset(
    {
        "lint.json",
        "rtl_identifier_check.json",
        "sim_compile.json",
        "sim_run.json",
        "synth.json",
        "testbench_static_check.json",
    }
)
MUTATION_ROOT_FILES = frozenset({"diagnosis.json"})
MUTATION_EVAL_FILES = frozenset(
    {
        "oracle_evidence.json",
        "sim_compile.json",
        "sim_run.json",
    }
)
EXCLUDED_NAMES = frozenset(
    {
        "sim.out",
        "pnr.log",
        "openxc7_design.json",
        "openxc7_routed.json",
        "openxc7_design.fasm",
    }
)
EXCLUDED_SUFFIXES = frozenset(
    {".bit", ".bin", ".dcp", ".fasm", ".memh", ".vcd"}
)
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
WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s\"'<>|,;)\]]+"
)
WSL_ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9_])/mnt/[A-Za-z]/[^\s\"'<>|,;)\]]+"
)
HOME_ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9_])/home/[^/\s\"'<>|]+/[^\s\"'<>|,;)\]]*"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def _repository_path(repository: Path, value: str, *, field: str) -> Path:
    relative = _safe_relative(value, field=field)
    candidate = (repository / Path(*relative.parts)).resolve()
    if not candidate.is_relative_to(repository):
        raise ValueError(f"{field} escapes repository: {value}")
    return candidate


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _sanitize_text(value: str, repository: Path) -> tuple[str, int]:
    replacements = 0
    result = value
    repository_variants = {
        str(repository),
        str(repository).replace("\\", "/"),
    }
    drive = repository.drive.rstrip(":").lower()
    if drive:
        parts = repository.parts[1:]
        repository_variants.add(
            f"/mnt/{drive}/" + "/".join(part for part in parts if part not in {"\\", "/"})
        )
    for variant in sorted(repository_variants, key=len, reverse=True):
        if not variant:
            continue
        result, count = re.subn(
            re.escape(variant),
            "<REPOSITORY_ROOT>",
            result,
            flags=re.IGNORECASE,
        )
        replacements += count
    for pattern in (
        WINDOWS_ABSOLUTE_PATH,
        WSL_ABSOLUTE_PATH,
        HOME_ABSOLUTE_PATH,
    ):
        result, count = pattern.subn("<ABSOLUTE_PATH>", result)
        replacements += count
    return result, replacements


def _sanitize_json_value(value: object, repository: Path) -> tuple[object, int]:
    if isinstance(value, dict):
        sanitized: dict[str, object] = {}
        replacements = 0
        for key, child in value.items():
            sanitized_child, child_replacements = _sanitize_json_value(
                child,
                repository,
            )
            sanitized[key] = sanitized_child
            replacements += child_replacements
        return sanitized, replacements
    if isinstance(value, list):
        sanitized_items: list[object] = []
        replacements = 0
        for child in value:
            sanitized_child, child_replacements = _sanitize_json_value(
                child,
                repository,
            )
            sanitized_items.append(sanitized_child)
            replacements += child_replacements
        return sanitized_items, replacements
    if isinstance(value, str):
        return _sanitize_text(value, repository)
    return value, 0


def _curate_bytes(path: Path, repository: Path) -> tuple[bytes, tuple[str, ...]]:
    raw = path.read_bytes()
    if b"\0" in raw:
        raise ValueError(f"binary evidence file is not publishable: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"non-UTF-8 evidence file is not publishable: {path}") from error

    transformations: list[str] = []
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(text)
        sanitized, replacements = _sanitize_json_value(payload, repository)
        curated = (
            json.dumps(
                sanitized,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        transformations.append("canonical_json")
    elif suffix == ".jsonl":
        lines: list[str] = []
        replacements = 0
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSONL evidence at {path}:{line_number}"
                ) from error
            sanitized, line_replacements = _sanitize_json_value(
                payload,
                repository,
            )
            replacements += line_replacements
            lines.append(
                json.dumps(
                    sanitized,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        curated = (("\n".join(lines) + "\n") if lines else "").encode("utf-8")
        transformations.append("canonical_jsonl")
    else:
        sanitized_text, replacements = _sanitize_text(text, repository)
        curated = sanitized_text.encode("utf-8")

    if replacements:
        transformations.append("redact_absolute_paths")
    if curated != raw and not transformations:
        transformations.append("normalized_text")
    return curated, tuple(transformations)


def _is_excluded(path: Path) -> bool:
    return path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES


def _load_source_groups(
    repository: Path,
    source_map_path: Path,
    plan: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    source_map = _load_json(source_map_path)
    if source_map.get("schema_version") != SOURCE_SCHEMA:
        raise ValueError("unexpected regenerated evidence source schema")
    raw_groups = source_map.get("groups")
    if not isinstance(raw_groups, list):
        raise ValueError("regenerated evidence groups must be a list")

    groups: dict[str, dict[str, Any]] = {}
    legacy_roots: set[str] = set()
    for raw_group in raw_groups:
        if not isinstance(raw_group, dict):
            raise ValueError("regenerated evidence group must be an object")
        run_id = str(raw_group.get("run_id", ""))
        if not run_id or PurePosixPath(run_id).name != run_id:
            raise ValueError(f"unsafe regenerated evidence run_id: {run_id!r}")
        if run_id in groups:
            raise ValueError(f"duplicate regenerated evidence run_id: {run_id}")
        legacy_root = _safe_relative(
            str(raw_group.get("legacy_source_root", "")),
            field="legacy_source_root",
        ).as_posix()
        if legacy_root in legacy_roots:
            raise ValueError(f"duplicate regenerated legacy source root: {legacy_root}")
        legacy_roots.add(legacy_root)
        candidate_root = _repository_path(
            repository,
            str(raw_group.get("candidate_root", "")),
            field="candidate_root",
        )
        run_root = _repository_path(
            repository,
            str(raw_group.get("run_root", "")),
            field="run_root",
        )
        if not candidate_root.is_dir():
            raise FileNotFoundError(f"candidate evidence root is missing: {candidate_root}")
        if not run_root.is_dir():
            raise FileNotFoundError(f"run evidence root is missing: {run_root}")
        summary = _load_json(run_root / "summary.json")
        if summary.get("run_id") != run_id:
            raise ValueError(f"regenerated summary run_id mismatch: {run_id}")
        strip_prefix = str(raw_group.get("strip_prefix", ""))
        if strip_prefix and (
            "\\" in strip_prefix
            or PurePosixPath(strip_prefix).is_absolute()
            or not strip_prefix.endswith("/")
        ):
            raise ValueError(f"unsafe regenerated strip_prefix: {strip_prefix!r}")
        raw_replacements = raw_group.get("replacements", [])
        if not isinstance(raw_replacements, list):
            raise ValueError(f"replacements must be a list: {run_id}")
        replacements: list[tuple[str, str]] = []
        for replacement in raw_replacements:
            if not isinstance(replacement, dict):
                raise ValueError(f"replacement must be an object: {run_id}")
            old = str(replacement.get("from", ""))
            new = str(replacement.get("to", ""))
            if not old or "\\" in old or "\\" in new:
                raise ValueError(f"unsafe regenerated replacement: {replacement!r}")
            replacements.append((old, new))
        groups[run_id] = {
            "run_id": run_id,
            "legacy_source_root": legacy_root,
            "candidate_root": candidate_root,
            "run_root": run_root,
            "strip_prefix": strip_prefix,
            "replacements": tuple(replacements),
        }

    plan_groups = plan.get("run_groups")
    if not isinstance(plan_groups, list):
        raise ValueError("legacy evidence run_groups must be a list")
    plan_run_ids = {
        str(group.get("run_id", ""))
        for group in plan_groups
        if isinstance(group, dict)
    }
    if plan_run_ids != groups.keys():
        missing = sorted(plan_run_ids - groups.keys())
        extra = sorted(groups.keys() - plan_run_ids)
        raise ValueError(
            f"regenerated source map does not match plan; missing={missing}, extra={extra}"
        )
    return groups


def _map_legacy_relative(group: dict[str, Any], value: str) -> PurePosixPath:
    mapped = value
    strip_prefix = group["strip_prefix"]
    if strip_prefix:
        if not mapped.startswith(strip_prefix):
            raise ValueError(
                f"legacy reference lacks required prefix {strip_prefix!r}: {value}"
            )
        mapped = mapped[len(strip_prefix) :]
    for old, new in group["replacements"]:
        mapped = mapped.replace(old, new)
    return _safe_relative(mapped, field="mapped_source_relative_path")


def _source_for_relative(
    group: dict[str, Any],
    relative: PurePosixPath,
) -> Path:
    if relative.parts[0] in {"dataset", "exports"}:
        base = group["candidate_root"]
        suffix = relative
    elif (
        len(relative.parts) >= 3
        and relative.parts[0] == "runs"
        and relative.parts[1] == group["run_id"]
    ):
        base = group["run_root"]
        suffix = PurePosixPath(*relative.parts[2:])
    else:
        raise ValueError(
            f"unsupported regenerated evidence relative path for {group['run_id']}: {relative}"
        )
    source = (base / Path(*suffix.parts)).resolve()
    if not source.is_relative_to(base):
        raise ValueError(f"regenerated evidence source escapes its root: {relative}")
    return source


def _relative_for_source(group: dict[str, Any], source: Path) -> PurePosixPath:
    source = source.resolve()
    candidate_root = group["candidate_root"]
    run_root = group["run_root"]
    if source.is_relative_to(candidate_root):
        return PurePosixPath(source.relative_to(candidate_root).as_posix())
    if source.is_relative_to(run_root):
        return (
            PurePosixPath("runs")
            / group["run_id"]
            / PurePosixPath(source.relative_to(run_root).as_posix())
        )
    raise ValueError(f"regenerated evidence source is outside configured roots: {source}")


def _destination_for_relative(
    run_id: str,
    relative: PurePosixPath,
) -> PurePosixPath:
    return CURATED_ROOT / run_id / relative


def _scan_content(data: bytes) -> tuple[bool, bool]:
    has_secret = any(pattern.search(data) for pattern in SECRET_PATTERNS)
    has_private_path = any(pattern.search(data) for pattern in PRIVATE_PATH_PATTERNS)
    return has_secret, has_private_path


def _ledger_references(ledger: dict[str, Any]) -> list[str]:
    families = ledger.get("task_families")
    if not isinstance(families, list):
        raise ValueError("task evidence ledger task_families must be a list")
    references: list[str] = []
    for family in families:
        if not isinstance(family, dict):
            raise ValueError("task evidence family must be an object")
        raw_references = family.get("evidence_refs")
        if not isinstance(raw_references, list) or not all(
            isinstance(reference, str) for reference in raw_references
        ):
            raise ValueError("task evidence evidence_refs must be string arrays")
        references.extend(raw_references)
    return references


def build_promotion_preview(
    repository: Path,
    *,
    plan_path: Path,
    source_map_path: Path,
    ledger_path: Path,
) -> dict[str, Any]:
    repository = repository.resolve()
    if not (repository / ".git").exists():
        raise ValueError(f"repository .git entry is missing: {repository}")
    plan_path = plan_path.resolve()
    source_map_path = source_map_path.resolve()
    ledger_path = ledger_path.resolve()
    for path, label in (
        (plan_path, "plan"),
        (source_map_path, "source map"),
        (ledger_path, "ledger"),
    ):
        if not path.is_relative_to(repository):
            raise ValueError(f"{label} must stay inside repository")

    plan = _load_json(plan_path)
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("unexpected legacy evidence migration schema")
    groups = _load_source_groups(repository, source_map_path, plan)
    ledger = _load_json(ledger_path)
    ledger_references = _ledger_references(ledger)

    selected: dict[str, dict[str, Any]] = {}
    destination_sources: dict[str, str] = {}
    reference_map: dict[str, str] = {}
    sample_ids_by_run: dict[str, set[str]] = {
        run_id: set() for run_id in groups
    }
    excluded_files: set[str] = set()

    def select_file(
        group: dict[str, Any],
        source: Path,
        reason: str,
        *,
        required: bool = True,
    ) -> None:
        if not source.exists():
            if required:
                raise FileNotFoundError(f"required regenerated evidence is missing: {source}")
            return
        if not source.is_file():
            raise ValueError(f"regenerated evidence is not a file: {source}")
        relative = _relative_for_source(group, source)
        destination = _destination_for_relative(
            group["run_id"],
            relative,
        ).as_posix()
        source_relative = source.relative_to(repository).as_posix()
        if _is_excluded(source):
            excluded_files.add(source_relative)
            if required:
                raise ValueError(f"required evidence is excluded from publication: {source}")
            return
        prior_source = destination_sources.get(destination)
        if prior_source is not None and prior_source != source_relative:
            raise ValueError(f"multiple sources map to evidence destination: {destination}")
        destination_sources[destination] = source_relative
        record = selected.get(source_relative)
        if record is None:
            selected[source_relative] = {
                "run_id": group["run_id"],
                "source_path": source_relative,
                "destination_path": destination,
                "selection_reasons": {reason},
            }
        else:
            if record["destination_path"] != destination:
                raise ValueError(f"evidence source maps to multiple destinations: {source}")
            record["selection_reasons"].add(reason)

    def select_tree(
        group: dict[str, Any],
        root: Path,
        reason: str,
        *,
        required: bool = True,
    ) -> None:
        if not root.exists():
            if required:
                raise FileNotFoundError(f"required regenerated evidence subtree is missing: {root}")
            return
        if not root.is_dir():
            raise ValueError(f"regenerated evidence subtree is not a directory: {root}")
        files = sorted(path for path in root.rglob("*") if path.is_file())
        selected_count = 0
        for path in files:
            if _is_excluded(path):
                excluded_files.add(path.relative_to(repository).as_posix())
                continue
            select_file(group, path, reason)
            selected_count += 1
        if required and selected_count == 0:
            raise ValueError(f"regenerated evidence subtree has no publishable files: {root}")

    def select_mutation_tree(
        group: dict[str, Any],
        root: Path,
    ) -> None:
        if not root.is_dir():
            raise FileNotFoundError(
                f"required regenerated mutation subtree is missing: {root}"
            )
        selected_count = 0
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
            relative = path.relative_to(root)
            parts = relative.parts
            allowed = (
                (len(parts) == 2 and parts[1] in MUTATION_ROOT_FILES)
                or (
                    len(parts) == 3
                    and parts[1] == "eval"
                    and parts[2] in MUTATION_EVAL_FILES
                )
                or (
                    len(parts) >= 3
                    and parts[1] in {"rtl", "sim"}
                    and path.suffix.lower() in {".v", ".sv"}
                )
            )
            if _is_excluded(path) or not allowed:
                excluded_files.add(path.relative_to(repository).as_posix())
                continue
            select_file(group, path, "ledger_reference")
            selected_count += 1
        if selected_count == 0:
            raise ValueError(
                f"regenerated mutation subtree has no publishable files: {root}"
            )

    def select_attempt_evidence(
        group: dict[str, Any],
        root: Path,
    ) -> None:
        if not root.is_dir():
            raise FileNotFoundError(
                f"required regenerated attempt evidence is missing: {root}"
            )
        selected_count = 0
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
            relative = path.relative_to(root)
            allowed = (
                len(relative.parts) == 1
                and relative.name in ATTEMPT_EVAL_FILES
            ) or (
                relative.as_posix()
                in {"oracle/evidence.json", "oracle/manifest.json"}
            )
            if _is_excluded(path) or not allowed:
                excluded_files.add(path.relative_to(repository).as_posix())
                continue
            select_file(group, path, "tool_evidence")
            selected_count += 1
        if selected_count == 0:
            raise ValueError(
                f"regenerated attempt evidence has no publishable files: {root}"
            )

    raw_plan_groups = plan.get("run_groups")
    if not isinstance(raw_plan_groups, list):
        raise ValueError("legacy evidence run_groups must be a list")
    reference_count = 0
    for raw_plan_group in raw_plan_groups:
        if not isinstance(raw_plan_group, dict):
            raise ValueError("legacy evidence run group must be an object")
        run_id = str(raw_plan_group.get("run_id", ""))
        group = groups[run_id]
        if raw_plan_group.get("source_root") != group["legacy_source_root"]:
            raise ValueError(f"legacy source root mismatch for run: {run_id}")
        references = raw_plan_group.get("references")
        if not isinstance(references, list):
            raise ValueError(f"legacy references must be a list: {run_id}")
        for reference in references:
            if not isinstance(reference, dict):
                raise ValueError("legacy evidence reference must be an object")
            old_reference = str(reference.get("source_reference", ""))
            source_relative = str(reference.get("source_relative_path", ""))
            expected_old_reference = (
                PurePosixPath(group["legacy_source_root"])
                / _safe_relative(
                    source_relative,
                    field="legacy_source_relative_path",
                )
            ).as_posix()
            if old_reference != expected_old_reference:
                raise ValueError(f"legacy source reference mismatch: {old_reference}")
            current_relative = _map_legacy_relative(group, source_relative)
            source = _source_for_relative(group, current_relative)
            destination_reference = _destination_for_relative(
                run_id,
                current_relative,
            ).as_posix()
            prior_destination = reference_map.get(old_reference)
            if (
                prior_destination is not None
                and prior_destination != destination_reference
            ):
                raise ValueError(
                    f"legacy reference maps to multiple destinations: {old_reference}"
                )
            reference_map[old_reference] = destination_reference
            reference_kind = str(reference.get("reference_kind", ""))
            if reference_kind == "file":
                select_file(group, source, "ledger_reference")
            elif reference_kind == "subtree":
                if current_relative.name != "oracle_mutations":
                    raise ValueError(
                        f"unsupported regenerated evidence subtree: {current_relative}"
                    )
                select_mutation_tree(group, source)
            else:
                raise ValueError(f"unsupported evidence reference kind: {reference_kind}")
            if (
                len(current_relative.parts) >= 2
                and current_relative.parts[0] == "dataset"
            ):
                sample_ids_by_run[run_id].add(current_relative.parts[1])
            reference_count += 1

    expected_reference_count = int(plan.get("planned_reference_count", -1))
    if reference_count != expected_reference_count:
        raise ValueError("migration plan reference count changed during promotion")

    for run_id, group in groups.items():
        for name in RUN_FILES:
            select_file(
                group,
                group["run_root"] / name,
                "run_provenance",
                required=name == "summary.json",
            )
        for sample_id in sorted(sample_ids_by_run[run_id]):
            sample_root = group["candidate_root"] / "dataset" / sample_id
            if not sample_root.is_dir():
                raise FileNotFoundError(
                    f"referenced regenerated sample is missing: {sample_root}"
                )
            for name in SAMPLE_ROOT_FILES:
                select_file(
                    group,
                    sample_root / name,
                    "sample_provenance",
                    required=name == "metadata.json",
                )
            select_tree(
                group,
                sample_root / "eval",
                "sample_verdict",
            )
            attempt_root = sample_root / "attempts" / "attempt_000"
            select_attempt_evidence(
                group,
                attempt_root / "eval",
            )
            for project_root in (
                attempt_root / "generated_project",
                sample_root / "final" / "generated_project",
            ):
                for name in ("manifest.json", "system_his.json"):
                    select_file(
                        group,
                        project_root / name,
                        "generated_project_contract",
                        required=False,
                    )
                for directory in GENERATED_PROJECT_DIRECTORIES:
                    select_tree(
                        group,
                        project_root / directory,
                        "generated_project_source",
                        required=False,
                    )
            openxc7_root = attempt_root / "generated_project" / "eval"
            for name in OPENXC7_EVIDENCE_FILES:
                select_file(
                    group,
                    openxc7_root / name,
                    "openxc7_physical_evidence",
                    required=False,
                )

    planned_references = set(reference_map)
    active_tmp_references = {
        reference for reference in ledger_references if reference.startswith("tmp/")
    }
    if active_tmp_references != planned_references:
        missing = sorted(active_tmp_references - planned_references)
        extra = sorted(planned_references - active_tmp_references)
        raise ValueError(
            f"migration plan does not cover active tmp references; missing={missing}, extra={extra}"
        )
    occurrence_count = sum(
        1 for reference in ledger_references if reference in planned_references
    )
    expected_occurrences = int(plan.get("reference_occurrence_count", -1))
    if occurrence_count != expected_occurrences:
        raise ValueError(
            "migration plan occurrence count does not match task evidence ledger"
        )

    secret_paths: list[str] = []
    private_paths: list[str] = []
    file_records: list[dict[str, Any]] = []
    for source_relative, record in sorted(
        selected.items(),
        key=lambda item: item[1]["destination_path"],
    ):
        source = repository / Path(*PurePosixPath(source_relative).parts)
        raw = source.read_bytes()
        curated, transformations = _curate_bytes(source, repository)
        raw_has_secret = any(pattern.search(raw) for pattern in SECRET_PATTERNS)
        curated_has_secret, curated_has_private_path = _scan_content(curated)
        if raw_has_secret or curated_has_secret:
            secret_paths.append(source_relative)
        if curated_has_private_path:
            private_paths.append(source_relative)
        destination = _repository_path(
            repository,
            record["destination_path"],
            field="destination_path",
        )
        curated_hash = _sha256_bytes(curated)
        if destination.exists():
            if not destination.is_file() or _sha256(destination) != curated_hash:
                raise ValueError(f"promotion destination conflicts: {destination}")
        file_records.append(
            {
                "run_id": record["run_id"],
                "source_path": source_relative,
                "destination_path": record["destination_path"],
                "selection_reasons": sorted(record["selection_reasons"]),
                "source_length": len(raw),
                "source_sha256": _sha256_bytes(raw),
                "curated_length": len(curated),
                "curated_sha256": curated_hash,
                "transformations": list(transformations),
            }
        )

    blocked = bool(secret_paths or private_paths)
    return {
        "schema_version": PROMOTION_SCHEMA,
        "mode": "preview",
        "status": "blocked_review" if blocked else "ready",
        "source_plan": plan_path.relative_to(repository).as_posix(),
        "source_plan_sha256": _sha256(plan_path),
        "source_map": source_map_path.relative_to(repository).as_posix(),
        "source_map_sha256": _sha256(source_map_path),
        "task_evidence_ledger": ledger_path.relative_to(repository).as_posix(),
        "task_evidence_ledger_sha256": _sha256(ledger_path),
        "run_count": len(groups),
        "reference_count": reference_count,
        "reference_occurrence_count": occurrence_count,
        "selected_file_count": len(file_records),
        "selected_source_bytes": sum(
            record["source_length"] for record in file_records
        ),
        "selected_curated_bytes": sum(
            record["curated_length"] for record in file_records
        ),
        "training_exports_promoted": False,
        "excluded_file_count": len(excluded_files),
        "excluded_files": sorted(excluded_files),
        "blocked_secret_paths": sorted(secret_paths),
        "blocked_private_path_files": sorted(private_paths),
        "reference_map": [
            {"source_reference": old, "destination_reference": new}
            for old, new in sorted(reference_map.items())
        ],
        "files": file_records,
    }


def _encode_task_evidence_ledger(ledger: dict[str, Any]) -> bytes:
    lines = ["{"]
    keys = list(ledger)
    for key_index, key in enumerate(keys):
        suffix = "," if key_index < len(keys) - 1 else ""
        if key != "task_families":
            encoded = json.dumps(
                ledger[key],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            lines.append(f"  {json.dumps(key)}: {encoded}{suffix}")
            continue
        families = ledger[key]
        if not isinstance(families, list):
            raise ValueError("task evidence ledger task_families must be a list")
        lines.append(f"  {json.dumps(key)}: [")
        for family_index, family in enumerate(families):
            family_suffix = "," if family_index < len(families) - 1 else ""
            encoded = json.dumps(
                family,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            lines.append(f"    {encoded}{family_suffix}")
        lines.append(f"  ]{suffix}")
    lines.append("}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def apply_promotion(
    repository: Path,
    preview: dict[str, Any],
) -> dict[str, Any]:
    repository = repository.resolve()
    if preview.get("schema_version") != PROMOTION_SCHEMA:
        raise ValueError("unexpected regenerated evidence promotion schema")
    if preview.get("status") != "ready":
        raise ValueError("regenerated evidence promotion preview is not ready")

    for path_field, hash_field in (
        ("source_plan", "source_plan_sha256"),
        ("source_map", "source_map_sha256"),
        ("task_evidence_ledger", "task_evidence_ledger_sha256"),
    ):
        path = _repository_path(
            repository,
            str(preview.get(path_field, "")),
            field=path_field,
        )
        if _sha256(path) != preview.get(hash_field):
            raise ValueError(f"promotion input changed after preview: {path_field}")

    raw_files = preview.get("files")
    if not isinstance(raw_files, list):
        raise ValueError("promotion preview files must be a list")
    operations: list[tuple[Path, Path, bytes, bool]] = []
    for record in raw_files:
        if not isinstance(record, dict):
            raise ValueError("promotion file record must be an object")
        source = _repository_path(
            repository,
            str(record.get("source_path", "")),
            field="source_path",
        )
        destination_relative = _safe_relative(
            str(record.get("destination_path", "")),
            field="destination_path",
        )
        if not destination_relative.is_relative_to(CURATED_ROOT):
            raise ValueError(
                f"promotion destination escapes curated root: {destination_relative}"
            )
        destination = _repository_path(
            repository,
            destination_relative.as_posix(),
            field="destination_path",
        )
        if not source.is_file():
            raise FileNotFoundError(f"promotion source is missing: {source}")
        raw = source.read_bytes()
        if _sha256_bytes(raw) != record.get("source_sha256"):
            raise ValueError(f"promotion source changed after preview: {source}")
        curated, _ = _curate_bytes(source, repository)
        if _sha256_bytes(curated) != record.get("curated_sha256"):
            raise ValueError(f"promotion curation changed after preview: {source}")
        has_secret, has_private_path = _scan_content(curated)
        if has_secret or has_private_path:
            raise ValueError(f"promotion content failed publication scan: {source}")
        reuse = destination.exists()
        if reuse and (
            not destination.is_file()
            or _sha256(destination) != record.get("curated_sha256")
        ):
            raise ValueError(f"promotion destination conflicts: {destination}")
        operations.append((source, destination, curated, reuse))

    copied = 0
    reused = 0
    for _, destination, curated, reuse in operations:
        if reuse:
            reused += 1
            continue
        _atomic_write(destination, curated)
        copied += 1

    reference_records = preview.get("reference_map")
    if not isinstance(reference_records, list):
        raise ValueError("promotion reference_map must be a list")
    reference_map: dict[str, str] = {}
    for record in reference_records:
        if not isinstance(record, dict):
            raise ValueError("promotion reference record must be an object")
        source_reference = str(record.get("source_reference", ""))
        destination_reference = str(record.get("destination_reference", ""))
        if source_reference in reference_map:
            raise ValueError(f"duplicate promotion source reference: {source_reference}")
        reference_map[source_reference] = destination_reference

    ledger_path = _repository_path(
        repository,
        str(preview.get("task_evidence_ledger", "")),
        field="task_evidence_ledger",
    )
    ledger = _load_json(ledger_path)
    families = ledger.get("task_families")
    if not isinstance(families, list):
        raise ValueError("task evidence ledger task_families must be a list")
    replaced = 0
    seen_sources: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            raise ValueError("task evidence family must be an object")
        references = family.get("evidence_refs")
        if not isinstance(references, list):
            raise ValueError("task evidence evidence_refs must be a list")
        rewritten: list[str] = []
        for reference in references:
            if not isinstance(reference, str):
                raise ValueError("task evidence evidence_refs must contain strings")
            replacement = reference_map.get(reference)
            if replacement is None:
                rewritten.append(reference)
            else:
                rewritten.append(replacement)
                seen_sources.add(reference)
                replaced += 1
        family["evidence_refs"] = rewritten
    if seen_sources != reference_map.keys():
        missing = sorted(reference_map.keys() - seen_sources)
        raise ValueError(f"promotion references were absent from ledger: {missing}")
    if replaced != preview.get("reference_occurrence_count"):
        raise ValueError("promotion reference occurrence count changed")
    remaining_tmp = [
        reference
        for reference in _ledger_references(ledger)
        if reference.startswith("tmp/")
    ]
    if remaining_tmp:
        raise ValueError(f"task evidence ledger still contains tmp references: {remaining_tmp}")
    _atomic_write(ledger_path, _encode_task_evidence_ledger(ledger))

    result = dict(preview)
    result.update(
        {
            "mode": "applied",
            "status": "pass",
            "copied_file_count": copied,
            "reused_file_count": reused,
            "rewritten_reference_occurrence_count": replaced,
            "task_evidence_ledger_after_sha256": _sha256(ledger_path),
        }
    )
    return result


def write_promotion(path: Path, promotion: dict[str, Any]) -> None:
    encoded = (
        json.dumps(
            promotion,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    _atomic_write(path, encoded)


def _inside_repository(repository: Path, candidate: Path, *, field: str) -> Path:
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (repository / candidate).resolve()
    )
    if not resolved.is_relative_to(repository):
        raise ValueError(f"{field} must stay inside repository")
    return resolved


def _output_path(repository: Path, candidate: Path, *, apply: bool) -> Path:
    output = _inside_repository(repository, candidate, field="output")
    allowed = (
        repository / "reports" / "reorganization"
        if apply
        else repository / "artifacts" / "reorganization" / "phase-b4"
    ).resolve()
    if not output.is_relative_to(allowed):
        mode = "applied" if apply else "preview"
        raise ValueError(
            f"{mode} promotion output must stay under "
            f"{allowed.relative_to(repository).as_posix()}/"
        )
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path(
            "reports/reorganization/legacy-active-evidence-migration.json"
        ),
    )
    parser.add_argument(
        "--source-map",
        type=Path,
        default=Path(
            "reports/reorganization/regenerated-evidence-sources.json"
        ),
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("docs/sr2fpga-task-evidence-v0.1.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/reorganization/phase-b4/"
            "regenerated-evidence-promotion-preview.json"
        ),
    )
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        repository = args.root.resolve()
        plan_path = _inside_repository(repository, args.plan, field="plan")
        source_map_path = _inside_repository(
            repository,
            args.source_map,
            field="source_map",
        )
        ledger_path = _inside_repository(repository, args.ledger, field="ledger")
        output_path = _output_path(
            repository,
            args.output,
            apply=args.apply,
        )
        preview = build_promotion_preview(
            repository,
            plan_path=plan_path,
            source_map_path=source_map_path,
            ledger_path=ledger_path,
        )
        result = apply_promotion(repository, preview) if args.apply else preview
        write_promotion(output_path, result)
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
