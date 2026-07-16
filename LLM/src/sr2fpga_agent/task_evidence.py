"""Runtime access to the SR2FPGA task-family evidence ledger."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .task_catalog import CATALOG_PATH
from .task_families import family_id_for_task_type
from .oracles.bundle import load_oracle_bundle


EVIDENCE_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "sr2fpga-task-evidence-v0.1.json"
)

GENERATOR_STATUSES = frozenset({"not_implemented", "implemented"})
TESTBENCH_STATUSES = frozenset({"not_implemented", "implemented"})
GOLDEN_MODEL_STATUSES = frozenset(
    {"none", "embedded_sv", "python_reference", "host_reference"}
)
MUTATION_STATUSES = frozenset({"not_run", "qualified", "unqualified"})
INDEPENDENT_ORACLE_STATUSES = frozenset({"not_run", "qualified", "unqualified"})
REQUIRED_ORACLE_SCENARIO_CLASSES = frozenset(
    {"public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress"}
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERIFIED_LEVELS = frozenset({"not_run", "L3", "L4", "L5"})
TOOL_STATUSES = frozenset({"pass", "fail", "not_run"})
VERIFICATION_LEVEL_RANK = {
    "GEN_FAIL": -1,
    "not_run": 0,
    "L0": 0,
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
    "L5": 5,
}


@dataclass(frozen=True)
class MutationEvidence:
    status: str
    score: float | None
    run_id: str


@dataclass(frozen=True)
class IndependentOracleEvidence:
    status: str
    run_id: str
    bundle_sha256: str
    scenario_classes: tuple[str, ...]
    hidden_vectors_exported: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_classes", tuple(self.scenario_classes))


@dataclass(frozen=True)
class TaskFamilyEvidence:
    family_id: str
    generator_status: str
    testbench_status: str
    golden_model_status: str
    mutation_evidence: MutationEvidence
    highest_verified_level: str
    l4_open_status: str
    l4_commercial_status: str
    l5_status: str
    last_verified_run: str
    evidence_refs: tuple[str, ...]
    independent_oracle_evidence: IndependentOracleEvidence = IndependentOracleEvidence(
        status="not_run",
        run_id="",
        bundle_sha256="",
        scenario_classes=(),
        hidden_vectors_exported=False,
    )

    def __post_init__(self) -> None:
        if isinstance(self.evidence_refs, str):
            raise TypeError("evidence_refs must contain strings")
        references = tuple(self.evidence_refs)
        if not all(isinstance(reference, str) for reference in references):
            raise TypeError("evidence_refs must contain strings")
        object.__setattr__(self, "evidence_refs", references)


def load_task_family_evidence(
    path: Path = EVIDENCE_PATH,
    *,
    catalog_path: Path = CATALOG_PATH,
) -> tuple[TaskFamilyEvidence, ...]:
    """Load and validate the task-family evidence ledger."""
    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    with catalog_path.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    entries = tuple(_parse_entry(item) for item in document["task_families"])
    validate_task_family_evidence(document, entries, catalog)
    return entries


def validate_task_family_evidence(
    document: dict[str, object],
    entries: tuple[TaskFamilyEvidence, ...],
    catalog: dict[str, object],
) -> None:
    """Reject evidence that disagrees with its declared catalog contract."""
    if document.get("schema_version") != "sr2fpga-task-evidence-v0.1":
        raise ValueError("invalid evidence schema_version")
    if document.get("source_catalog") != "docs/sr2fpga-task-catalog-v0.2.json":
        raise ValueError("invalid evidence source_catalog")

    families = catalog["task_families"]
    catalog_ids = [family["family_id"] for family in families]
    if len(catalog_ids) != len(set(catalog_ids)):
        raise ValueError("duplicate catalog family_ids")

    evidence_ids = [entry.family_id for entry in entries]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("duplicate evidence family_ids")
    missing = sorted(set(catalog_ids) - set(evidence_ids))
    if missing:
        raise ValueError(f"missing evidence family_ids: {', '.join(missing)}")
    unexpected = sorted(set(evidence_ids) - set(catalog_ids))
    if unexpected:
        raise ValueError(f"unexpected evidence family_ids: {', '.join(unexpected)}")

    aliases_by_family = {
        family["family_id"]: tuple(family.get("current_generator_aliases", []))
        for family in families
    }
    for entry in entries:
        _validate_entry(entry, aliases_by_family[entry.family_id])


def _parse_entry(item: dict[str, object]) -> TaskFamilyEvidence:
    mutation = item["mutation_evidence"]
    score = mutation["score"]
    if isinstance(score, (int, float)) and not isinstance(score, bool):
        score = float(score)
    independent_oracle = item.get(
        "independent_oracle_evidence",
        {
            "status": "not_run",
            "run_id": "",
            "bundle_sha256": "",
            "scenario_classes": [],
            "hidden_vectors_exported": False,
        },
    )
    if not isinstance(independent_oracle, dict):
        raise ValueError("independent_oracle_evidence must be an object")
    return TaskFamilyEvidence(
        family_id=item["family_id"],
        generator_status=item["generator_status"],
        testbench_status=item["testbench_status"],
        golden_model_status=item["golden_model_status"],
        mutation_evidence=MutationEvidence(
            status=mutation["status"],
            score=score,
            run_id=mutation["run_id"],
        ),
        highest_verified_level=item["highest_verified_level"],
        l4_open_status=item["l4_open_status"],
        l4_commercial_status=item["l4_commercial_status"],
        l5_status=item["l5_status"],
        last_verified_run=item["last_verified_run"],
        evidence_refs=tuple(item["evidence_refs"]),
        independent_oracle_evidence=IndependentOracleEvidence(
            status=independent_oracle.get("status"),
            run_id=independent_oracle.get("run_id"),
            bundle_sha256=independent_oracle.get("bundle_sha256"),
            scenario_classes=tuple(independent_oracle.get("scenario_classes", ())),
            hidden_vectors_exported=independent_oracle.get("hidden_vectors_exported"),
        ),
    )


def _validate_entry(entry: TaskFamilyEvidence, aliases: tuple[str, ...]) -> None:
    _require_status(entry.generator_status, GENERATOR_STATUSES, "generator_status")
    _require_status(entry.testbench_status, TESTBENCH_STATUSES, "testbench_status")
    _require_status(entry.golden_model_status, GOLDEN_MODEL_STATUSES, "golden_model_status")
    _require_status(entry.highest_verified_level, VERIFIED_LEVELS, "highest_verified_level")
    _require_status(entry.l4_open_status, TOOL_STATUSES, "l4_open_status")
    _require_status(entry.l4_commercial_status, TOOL_STATUSES, "l4_commercial_status")
    _require_status(entry.l5_status, TOOL_STATUSES, "l5_status")
    _require_status(entry.mutation_evidence.status, MUTATION_STATUSES, "mutation status")
    _validate_independent_oracle(entry)

    if entry.generator_status == "implemented" and not aliases:
        raise ValueError("implemented generator has no catalog alias")
    if (
        entry.testbench_status == "implemented"
        and entry.generator_status != "implemented"
    ):
        raise ValueError("implemented testbench requires implemented generator")
    if entry.highest_verified_level != "not_run" and (
        entry.generator_status != "implemented"
        or entry.testbench_status != "implemented"
    ):
        raise ValueError(
            f"{entry.highest_verified_level} evidence requires implemented generator and testbench"
        )
    if (
        entry.l4_open_status == "pass" or entry.l4_commercial_status == "pass"
    ) and entry.highest_verified_level not in {"L4", "L5"}:
        raise ValueError("L4 pass requires highest level L4 or L5")
    if entry.l5_status == "pass" and entry.highest_verified_level != "L5":
        raise ValueError("L5 pass requires highest level L5")

    mutation = entry.mutation_evidence
    if mutation.status == "qualified" and not (
        isinstance(mutation.score, float)
        and 0.0 <= mutation.score <= 1.0
        and isinstance(mutation.run_id, str)
        and mutation.run_id
    ):
        raise ValueError("qualified mutation requires score in [0,1] and non-empty run_id")
    if mutation.status == "not_run" and (
        mutation.score is not None or mutation.run_id != ""
    ):
        raise ValueError("not_run mutation requires null score and empty run_id")

    _require_trimmed(entry.last_verified_run)
    _require_trimmed(mutation.run_id)
    for reference in entry.evidence_refs:
        _require_trimmed(reference)


def _validate_independent_oracle(entry: TaskFamilyEvidence) -> None:
    oracle = entry.independent_oracle_evidence
    _require_status(
        oracle.status,
        INDEPENDENT_ORACLE_STATUSES,
        "independent oracle status",
    )
    if not isinstance(oracle.hidden_vectors_exported, bool):
        raise ValueError("independent oracle hidden_vectors_exported must be boolean")
    if not all(isinstance(item, str) for item in oracle.scenario_classes):
        raise ValueError("independent oracle scenario_classes must contain strings")
    _require_trimmed(oracle.run_id)
    _require_trimmed(oracle.bundle_sha256)

    if oracle.status == "not_run":
        if (
            oracle.run_id
            or oracle.bundle_sha256
            or oracle.scenario_classes
            or oracle.hidden_vectors_exported
        ):
            raise ValueError("not_run independent oracle requires empty provenance")
        return
    if oracle.status != "qualified":
        return
    if entry.golden_model_status != "python_reference":
        raise ValueError("qualified independent oracle requires golden_model_status=python_reference")
    if not oracle.run_id or not SHA256_RE.fullmatch(oracle.bundle_sha256):
        raise ValueError(
            "qualified independent oracle requires non-empty run_id and bundle_sha256"
        )
    classes = set(oracle.scenario_classes)
    if classes != REQUIRED_ORACLE_SCENARIO_CLASSES or len(oracle.scenario_classes) != len(classes):
        raise ValueError("qualified independent oracle requires all scenario classes")
    if oracle.hidden_vectors_exported:
        raise ValueError("qualified independent oracle must not export hidden vectors")
    if entry.last_verified_run != oracle.run_id:
        raise ValueError("qualified independent oracle run_id must match last_verified_run")


def _require_status(value: str, allowed: frozenset[str], field: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"invalid {field}: {value}")


def _require_trimmed(value: str) -> None:
    if not isinstance(value, str) or value != value.strip():
        raise ValueError("provenance strings must be trimmed")


def render_task_evidence_markdown(
    *,
    catalog_path: Path = CATALOG_PATH,
    evidence_path: Path = EVIDENCE_PATH,
) -> str:
    """Render target, implementation, and verification views in catalog order."""
    with catalog_path.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    entries = load_task_family_evidence(evidence_path, catalog_path=catalog_path)
    evidence_by_family = {entry.family_id: entry for entry in entries}
    families = catalog["task_families"]
    paper1_core = catalog["recommended_sets"]["paper1_core"]

    implemented = sum(
        entry.generator_status == "implemented" for entry in entries
    )
    paper1_implemented = sum(
        evidence_by_family[family_id].generator_status == "implemented"
        for family_id in paper1_core
    )
    mutation_qualified = sum(
        entry.mutation_evidence.status == "qualified" for entry in entries
    )
    independent_oracle_qualified = sum(
        entry.independent_oracle_evidence.status == "qualified" for entry in entries
    )
    open_l4_pass = sum(entry.l4_open_status == "pass" for entry in entries)
    commercial_l4_pass = sum(
        entry.l4_commercial_status == "pass" for entry in entries
    )
    l5_pass = sum(entry.l5_status == "pass" for entry in entries)

    lines = [
        "# SR2FPGA Task Evidence Status",
        "",
        "Generated from the task catalog and evidence ledger. Target intent, "
        "current implementation, and verification proof are reported separately.",
        "",
        "## Summary",
        "",
        "| Measure | Value |",
        "| --- | --- |",
        _markdown_row("Catalog families", str(len(families))),
        _markdown_row("Implemented families", f"{implemented} / {len(families)}"),
        _markdown_row(
            "Paper 1 core implemented", f"{paper1_implemented} / {len(paper1_core)}"
        ),
        _markdown_row("Mutation-qualified families", str(mutation_qualified)),
        _markdown_row(
            "Independent Python oracle qualified", str(independent_oracle_qualified)
        ),
        _markdown_row("OpenXC7 L4 pass", str(open_l4_pass)),
        _markdown_row("Commercial L4 pass", str(commercial_l4_pass)),
        _markdown_row("L5 pass", str(l5_pass)),
        "",
        "## Target Task Map",
        "",
        "| Family | Task kind | Tier | Benchmark role | Intended oracle |",
        "| --- | --- | --- | --- | --- |",
    ]
    for family in families:
        lines.append(
            _markdown_row(
                family["family_id"],
                family["task_kind"],
                family["sr2fpga_tier"],
                family["benchmark_role"],
                ", ".join(family["oracle_kind"]),
            )
        )

    lines.extend(
        [
            "",
            "## Current Implementation Matrix",
            "",
            "| Family | Generator | Testbench | Golden model |",
            "| --- | --- | --- | --- |",
        ]
    )
    for family in families:
        entry = evidence_by_family[family["family_id"]]
        lines.append(
            _markdown_row(
                entry.family_id,
                entry.generator_status,
                entry.testbench_status,
                entry.golden_model_status,
            )
        )

    lines.extend(
        [
            "",
            "## Verification Evidence Matrix",
            "",
            "| Family | Mutation | Score | Independent oracle | Level | L4-open | L4-commercial | L5 | Run |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for family in families:
        entry = evidence_by_family[family["family_id"]]
        mutation = entry.mutation_evidence
        mutation_label = mutation.status
        if mutation.run_id:
            mutation_label = f"{mutation_label} ({mutation.run_id})"
        lines.append(
            _markdown_row(
                entry.family_id,
                mutation_label,
                "-" if mutation.score is None else f"{mutation.score:g}",
                entry.independent_oracle_evidence.status,
                entry.highest_verified_level,
                entry.l4_open_status,
                entry.l4_commercial_status,
                entry.l5_status,
                entry.last_verified_run or "-",
            )
        )

    lines.extend(
        [
            "",
            "## Paper 1 Closure Gaps",
            "",
            "| Family | Generator | Testbench | Highest verified level |",
            "| --- | --- | --- | --- |",
        ]
    )
    for family_id in paper1_core:
        entry = evidence_by_family[family_id]
        if entry.generator_status != "implemented":
            lines.append(
                _markdown_row(
                    entry.family_id,
                    entry.generator_status,
                    entry.testbench_status,
                    entry.highest_verified_level,
                )
            )

    return "\n".join(lines) + "\n"


def audit_local_run_artifacts(
    entries: Sequence[TaskFamilyEvidence], run_root: Path
) -> tuple[str, ...]:
    """Audit declared runs and artifact-backed qualified evidence locally."""
    declared_run_ids = _declared_run_ids(entries)
    summaries: dict[str, dict[str, object]] = {}
    run_root = Path(run_root)
    if run_root.is_dir():
        for summary_path in run_root.rglob("summary.json"):
            try:
                with summary_path.open(encoding="utf-8") as handle:
                    summary = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            run_id = summary.get("run_id") if isinstance(summary, dict) else None
            if isinstance(run_id, str):
                summaries.setdefault(run_id, summary)

    issues = [
        f"missing local summary.json for declared run_id: {run_id}"
        for run_id in declared_run_ids
        if run_id not in summaries
    ]
    for entry in entries:
        issues.extend(_audit_entry_artifacts(entry, summaries.get(entry.last_verified_run)))
    return tuple(issues)


def _audit_entry_artifacts(
    entry: TaskFamilyEvidence, summary: dict[str, object] | None
) -> list[str]:
    trajectory_paths = [
        _resolve_evidence_ref(reference)
        for reference in entry.evidence_refs
        if Path(reference).name == "trajectory.json"
    ]
    mutation_roots = [
        _resolve_evidence_ref(reference)
        for reference in entry.evidence_refs
        if Path(reference).name == "oracle_mutations"
    ]
    if not trajectory_paths and not mutation_roots:
        return []

    issues: list[str] = []
    qualified_independent_oracle = (
        entry.independent_oracle_evidence.status == "qualified"
    )
    if entry.mutation_evidence.status == "qualified" or qualified_independent_oracle:
        if not trajectory_paths:
            issues.append(f"qualified evidence missing trajectory.json for family_id: {entry.family_id}")
    if entry.mutation_evidence.status == "qualified":
        if not mutation_roots:
            issues.append(f"qualified evidence missing oracle_mutations for family_id: {entry.family_id}")
        if entry.mutation_evidence.run_id != entry.last_verified_run:
            issues.append(f"qualified evidence run_id differs from last_verified_run for family_id: {entry.family_id}")

    for trajectory_path in trajectory_paths:
        issues.extend(_audit_trajectory(entry, summary, trajectory_path, mutation_roots))
    for mutation_root in mutation_roots:
        if not mutation_root.is_dir():
            issues.append(f"missing oracle_mutations evidence artifact: {mutation_root}")
    return issues


def _audit_trajectory(
    entry: TaskFamilyEvidence,
    summary: dict[str, object] | None,
    trajectory_path: Path,
    mutation_roots: list[Path],
) -> list[str]:
    if not trajectory_path.is_file():
        return [f"missing trajectory.json evidence artifact: {trajectory_path}"]
    try:
        with trajectory_path.open(encoding="utf-8") as handle:
            trajectory = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return [f"unreadable trajectory.json evidence artifact: {trajectory_path}"]
    if not isinstance(trajectory, dict):
        return [f"invalid trajectory.json evidence artifact: {trajectory_path}"]

    issues: list[str] = []
    sample_dir = trajectory_path.parent.parent
    sample_id = trajectory.get("sample_id")
    if not isinstance(sample_id, str) or sample_id != sample_dir.name:
        issues.append(f"trajectory sample_id does not match evidence path: {trajectory_path}")
        return issues
    if summary is None or sample_id not in _summary_sample_ids(summary):
        issues.append(
            f"trajectory sample_id is not recorded by summary run_id: {entry.last_verified_run}"
        )
    issues.extend(_audit_sample_labels(entry, summary, sample_dir))

    metadata_path = sample_dir / "metadata.json"
    try:
        with metadata_path.open(encoding="utf-8") as handle:
            metadata = json.load(handle)
    except (OSError, json.JSONDecodeError):
        issues.append(f"missing or unreadable sample metadata for trajectory: {trajectory_path}")
        metadata = None
    if isinstance(metadata, dict) and metadata.get("family_id") != entry.family_id:
        issues.append(f"sample metadata family_id does not match ledger family_id: {entry.family_id}")

    oracle = trajectory.get("oracle_strength")
    if not isinstance(oracle, dict):
        issues.append(f"trajectory missing oracle_strength for family_id: {entry.family_id}")
        return issues
    if _canonical_family_id(oracle.get("task_family")) != entry.family_id:
        issues.append(f"trajectory task_family does not match ledger family_id: {entry.family_id}")
    if entry.mutation_evidence.status == "qualified":
        issues.extend(_audit_qualified_oracle(entry, oracle, sample_dir, mutation_roots))
    if entry.independent_oracle_evidence.status == "qualified":
        issues.extend(_audit_qualified_independent_oracle(entry, trajectory, sample_dir))
    return issues


def _audit_sample_labels(
    entry: TaskFamilyEvidence, summary: dict[str, object] | None, sample_dir: Path
) -> list[str]:
    labels_path = sample_dir / "eval" / "labels.json"
    try:
        with labels_path.open(encoding="utf-8") as handle:
            labels = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return [f"missing or unreadable labels.json for sample: {sample_dir.name}"]
    if not isinstance(labels, dict):
        return [f"invalid labels.json for sample: {sample_dir.name}"]

    expected_rank = VERIFICATION_LEVEL_RANK[entry.highest_verified_level]
    levels = (labels.get("pass_level"), labels.get("highest_official_level"))
    if not all(isinstance(level, str) and level in VERIFICATION_LEVEL_RANK for level in levels):
        return [f"labels.json has invalid verification level for sample: {sample_dir.name}"]

    issues: list[str] = []
    if any(VERIFICATION_LEVEL_RANK[level] < expected_rank for level in levels):
        issues.append(
            f"sample labels do not reach ledger highest_verified_level for family_id: {entry.family_id}"
        )
    if entry.highest_verified_level == "L3" and (
        summary is None or sample_dir.name not in _summary_success_l3_ids(summary)
    ):
        issues.append(
            f"L3 ledger evidence is not in summary success_l3 bucket for family_id: {entry.family_id}"
        )
    return issues


def _audit_qualified_oracle(
    entry: TaskFamilyEvidence,
    oracle: dict[str, object],
    sample_dir: Path,
    mutation_roots: list[Path],
) -> list[str]:
    expected_root = sample_dir / "oracle_mutations"
    if not any(_same_path(path, expected_root) for path in mutation_roots):
        return [f"oracle_mutations evidence path does not belong to trajectory sample: {sample_dir.name}"]

    details = oracle.get("mutation_details")
    mutation_cases = oracle.get("mutation_cases")
    killed = oracle.get("killed")
    score = oracle.get("mutation_score")
    survivors = oracle.get("surviving_mutations")
    non_scoreable = oracle.get("non_scoreable_mutations")
    if not (
        isinstance(details, dict)
        and isinstance(mutation_cases, int)
        and isinstance(killed, int)
        and isinstance(score, (int, float))
        and not isinstance(score, bool)
        and isinstance(survivors, list)
        and isinstance(non_scoreable, list)
    ):
        return [f"qualified trajectory has invalid oracle_strength fields for family_id: {entry.family_id}"]

    issues: list[str] = []
    if float(score) != entry.mutation_evidence.score:
        issues.append(f"trajectory mutation_score does not match ledger score for family_id: {entry.family_id}")
    all_killed = (
        mutation_cases == len(details)
        and killed == mutation_cases
        and mutation_cases > 0
        and not survivors
        and not non_scoreable
        and all(
            isinstance(detail, dict) and detail.get("outcome") == "killed"
            for detail in details.values()
        )
    )
    if not all_killed:
        issues.append(f"declared mutations are not all scoreable and killed for family_id: {entry.family_id}")
    for name, detail in details.items():
        artifact_dir = detail.get("artifact_dir") if isinstance(detail, dict) else None
        artifact_path = sample_dir / artifact_dir if isinstance(artifact_dir, str) else None
        if (
            artifact_path is None
            or not _is_within(artifact_path, expected_root)
            or not artifact_path.is_dir()
        ):
            issues.append(f"missing declared mutation artifact for {name}: {artifact_path}")
    return issues


def _audit_qualified_independent_oracle(
    entry: TaskFamilyEvidence,
    trajectory: dict[str, object],
    sample_dir: Path,
) -> list[str]:
    oracle = entry.independent_oracle_evidence
    profile = trajectory.get("oracle_profile")
    if not isinstance(profile, dict):
        return [f"qualified independent oracle missing oracle_profile for family_id: {entry.family_id}"]

    issues: list[str] = []
    if profile.get("hidden_vectors_exported") is not False:
        issues.append(
            f"qualified independent oracle hidden vectors were exported for family_id: {entry.family_id}"
        )
    if profile.get("kind") != "python_reference":
        issues.append(
            f"qualified independent oracle profile kind is not python_reference for family_id: {entry.family_id}"
        )
    if profile.get("family_id") != entry.family_id:
        issues.append(
            f"qualified independent oracle profile family_id does not match ledger family_id: {entry.family_id}"
        )

    oracle_root = sample_dir / "attempts" / "attempt_000" / "eval" / "oracle"
    try:
        bundle = load_oracle_bundle(oracle_root)
    except ValueError as exc:
        return issues + [
            f"qualified independent oracle bundle is invalid for family_id: {entry.family_id}: {exc}"
        ]
    if bundle.family_id != entry.family_id:
        issues.append(
            f"qualified independent oracle bundle family_id does not match ledger family_id: {entry.family_id}"
        )
    for source, bundle_sha256 in (
        ("ledger", oracle.bundle_sha256),
        ("trajectory", profile.get("bundle_sha256")),
    ):
        if bundle_sha256 != bundle.bundle_sha256:
            issues.append(
                f"qualified independent oracle bundle_sha256 does not match {source} for family_id: {entry.family_id}"
            )
    issues.extend(
        _audit_oracle_scenario_classes(
            profile,
            "trajectory oracle_profile",
            entry.family_id,
        )
    )
    bundle_classes = {scenario.scenario_class for scenario in bundle.scenarios}
    if bundle_classes != REQUIRED_ORACLE_SCENARIO_CLASSES:
        issues.append(
            f"qualified independent oracle bundle is missing scenario classes for family_id: {entry.family_id}"
        )

    evidence_path = oracle_root / "evidence.json"
    try:
        with evidence_path.open(encoding="utf-8") as handle:
            evidence = json.load(handle)
    except (OSError, json.JSONDecodeError):
        legacy_path = oracle_root / "results.json"
        diagnostic = (
            f"; obsolete results.json exists at {legacy_path}"
            if legacy_path.is_file()
            else ""
        )
        return issues + [
            f"missing or unreadable independent oracle evidence.json for family_id: {entry.family_id}{diagnostic}"
        ]
    if not isinstance(evidence, dict):
        return issues + [
            f"invalid independent oracle evidence.json for family_id: {entry.family_id}"
        ]
    if evidence.get("family_id") != entry.family_id:
        issues.append(
            f"independent oracle evidence family_id does not match ledger family_id: {entry.family_id}"
        )
    if evidence.get("bundle_sha256") != bundle.bundle_sha256:
        issues.append(
            f"qualified independent oracle bundle_sha256 does not match evidence.json for family_id: {entry.family_id}"
        )
    if evidence.get("status") not in {"pass", "passed"}:
        issues.append(
            f"qualified independent oracle evidence status is not passed for family_id: {entry.family_id}"
        )
    issues.extend(
        _audit_oracle_scenario_classes(
            evidence,
            "oracle evidence.json",
            entry.family_id,
        )
    )
    return issues


def _audit_oracle_scenario_classes(
    source: dict[str, object],
    label: str,
    family_id: str,
) -> list[str]:
    counts = source.get("scenario_counts")
    statuses = source.get("class_status")
    if not isinstance(counts, dict) or not isinstance(statuses, dict):
        return [f"qualified independent oracle {label} has invalid scenario classes for family_id: {family_id}"]
    issues: list[str] = []
    for scenario_class in REQUIRED_ORACLE_SCENARIO_CLASSES:
        if not isinstance(counts.get(scenario_class), int) or counts[scenario_class] <= 0:
            issues.append(
                f"qualified independent oracle {label} is missing scenario class {scenario_class} for family_id: {family_id}"
            )
        if statuses.get(scenario_class) not in {"pass", "passed"}:
            issues.append(
                f"qualified independent oracle {label} did not pass scenario class {scenario_class} for family_id: {family_id}"
            )
    return issues


def _summary_sample_ids(summary: dict[str, object]) -> set[str]:
    buckets = summary.get("buckets")
    if not isinstance(buckets, dict):
        return set()
    return {
        sample_id
        for bucket in buckets.values()
        if isinstance(bucket, list)
        for sample_id in bucket
        if isinstance(sample_id, str)
    }


def _summary_success_l3_ids(summary: dict[str, object]) -> set[str]:
    buckets = summary.get("buckets")
    if not isinstance(buckets, dict):
        return set()
    success_l3 = buckets.get("success_l3")
    return {sample_id for sample_id in success_l3 if isinstance(sample_id, str)} if isinstance(success_l3, list) else set()


def _resolve_evidence_ref(reference: str) -> Path:
    path = Path(reference)
    return path if path.is_absolute() else EVIDENCE_PATH.parent.parent / path


def _same_path(left: Path, right: Path) -> bool:
    return left.resolve() == right.resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _canonical_family_id(task_family: object) -> str | None:
    if not isinstance(task_family, str):
        return None
    try:
        return family_id_for_task_type(task_family)
    except KeyError:
        return task_family


def main(argv: Sequence[str] | None = None) -> int:
    """Render the ledger, with optional local run-artifact auditing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit-run-root", type=Path)
    args = parser.parse_args(argv)

    entries = load_task_family_evidence()
    markdown = render_task_evidence_markdown()
    if args.output is None:
        print(markdown, end="")
    else:
        if args.output.resolve() == EVIDENCE_PATH.resolve():
            parser.error("--output must not overwrite the evidence ledger")
        args.output.write_text(markdown, encoding="utf-8")

    if args.audit_run_root is None:
        return 0
    issues = audit_local_run_artifacts(entries, args.audit_run_root)
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1 if issues else 0


def _declared_run_ids(entries: Sequence[TaskFamilyEvidence]) -> tuple[str, ...]:
    run_ids: list[str] = []
    for entry in entries:
        for run_id in (
            entry.last_verified_run,
            entry.mutation_evidence.run_id,
            entry.independent_oracle_evidence.run_id,
        ):
            if run_id and run_id not in run_ids:
                run_ids.append(run_id)
    return tuple(run_ids)


def _markdown_row(*values: str) -> str:
    return "| " + " | ".join(values) + " |"


if __name__ == "__main__":
    raise SystemExit(main())
