"""Independent integrity audit for the frozen SR2FPGA Phase D pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(
    os.environ.get("SR2FPGA_REPO_ROOT", Path(__file__).resolve().parents[2])
).expanduser().resolve()
AGENT_SOURCE_ROOT = REPO_ROOT / "agent" / "src"
if str(AGENT_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_SOURCE_ROOT))

from sr2fpga_agent.measurement_freeze import freeze_fingerprint


EXPECTED_SOURCES = {"claude", "gpt", "qwen", "deepseek"}
EXPECTED_EPISODES = 24
EXPECTED_PAIRS = 6
MAX_L4_RUNS = 4
_SECRET_PATTERNS = (
    re.compile(rb"authorization\s*[:=]\s*bearer\s+\S+", re.IGNORECASE),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(rb"[\"']?(?:api_key|access_token|client_secret|password)[\"']?\s*[:=]", re.IGNORECASE),
)
_TRUSTED_PATH_PARTS = (
    "hidden",
    "golden",
    "scoreboard",
    "oracle",
    "board_constraints",
    "board_shell",
    "data_release",
)


def audit_run(run_root: Path) -> dict[str, Any]:
    """Audit run artifacts independently and return a machine-readable verdict."""
    run_root = run_root.resolve()
    config = _read_json(run_root / "config.json")
    state = _read_json(run_root / "run_state.json")
    freeze = _read_json(run_root / "measurement_freeze.json")
    paired = _read_json(run_root / "paired_results.json")
    summary = _read_json(run_root / "summary.json")
    dataset_root = Path(str(config.get("dataset_root", "")))
    if not dataset_root.is_absolute():
        dataset_root = (Path.cwd() / dataset_root).resolve()
    sample_ids = [str(item) for item in state.get("completed_samples", [])]
    samples = [_read_sample(dataset_root / sample_id, sample_id) for sample_id in sample_ids]

    checks: dict[str, dict[str, Any]] = {}
    blocking: list[str] = []

    scoreable_count = sum(int(sample["measurement"].get("scoreable") is True) for sample in samples)
    _record(
        checks,
        blocking,
        "scoreable_episode_count",
        scoreable_count == EXPECTED_EPISODES,
        actual=scoreable_count,
        expected=EXPECTED_EPISODES,
    )

    pairs = _group_samples(samples, "paired_requirement_id")
    complete_pair_count = sum(
        int(len(members) == 4 and {member["source"] for member in members} == EXPECTED_SOURCES)
        for members in pairs.values()
    )
    _record(
        checks,
        blocking,
        "complete_pairs",
        len(pairs) == EXPECTED_PAIRS and complete_pair_count == EXPECTED_PAIRS,
        actual=complete_pair_count,
        expected=EXPECTED_PAIRS,
    )

    requirement_mismatches = [
        pair_id
        for pair_id, members in pairs.items()
        if len({member["requirement_sha256"] for member in members}) != 1
    ]
    _record(
        checks,
        blocking,
        "same_requirement_per_pair",
        not requirement_mismatches,
        mismatched_pairs=requirement_mismatches,
    )

    stored_fingerprint = str(freeze.get("freeze_fingerprint", ""))
    freeze_samples = {
        str(item.get("sample_id")): item
        for item in freeze.get("samples", [])
        if isinstance(item, dict) and item.get("sample_id")
    }
    freeze_sample_ids = {
        sample_id for sample_id in freeze_samples
    }
    metadata_fingerprints = {str(sample["freeze_fingerprint"]) for sample in samples}
    freeze_ok = (
        bool(stored_fingerprint)
        and stored_fingerprint == freeze_fingerprint(freeze)
        and set(sample_ids) == freeze_sample_ids
        and metadata_fingerprints == {stored_fingerprint}
        and summary.get("freeze_fingerprint") == stored_fingerprint
    )
    _record(
        checks,
        blocking,
        "freeze_consistency",
        freeze_ok,
        stored_fingerprint=stored_fingerprint,
        metadata_fingerprints=sorted(metadata_fingerprints),
    )

    frozen_identity_violations: list[str] = []
    frozen_fields = (
        "source",
        "family_id",
        "paired_requirement_id",
        "requirement_sha256",
    )
    for sample in samples:
        sample_id = sample["sample_id"]
        frozen_sample = freeze_samples.get(sample_id)
        if frozen_sample is None:
            frozen_identity_violations.append(f"{sample_id}:missing_freeze_entry")
            continue
        for field in frozen_fields:
            if str(sample["metadata"].get(field, "")) != str(frozen_sample.get(field, "")):
                frozen_identity_violations.append(f"{sample_id}:{field}")
        requirement_path = sample["sample_dir"] / "requirement.txt"
        try:
            requirement = requirement_path.read_text(encoding="utf-8").rstrip()
        except (OSError, UnicodeDecodeError):
            frozen_identity_violations.append(f"{sample_id}:requirement_unreadable")
            continue
        actual_hash = hashlib.sha256(requirement.encode("utf-8")).hexdigest()
        if actual_hash != str(frozen_sample.get("requirement_sha256", "")):
            frozen_identity_violations.append(f"{sample_id}:requirement_file_hash")
    _record(
        checks,
        blocking,
        "frozen_sample_identity",
        not frozen_identity_violations,
        violating_samples=frozen_identity_violations,
    )

    same_source_violations: list[str] = []
    for sample in samples:
        if (
            sample["metadata"].get("repair_provider_policy") != "same_as_source"
            or sample["metadata"].get("repair_provider_resolved") != sample["source"]
        ):
            same_source_violations.append(f"{sample['sample_id']}:metadata")
        repair_attempts = int(sample["measurement"].get("repair_attempts_used", 0) or 0)
        if repair_attempts <= 0:
            continue
        patches = sample["trajectory"].get("patches", [])
        if not isinstance(patches, list) or len(patches) < repair_attempts:
            same_source_violations.append(f"{sample['sample_id']}:missing_patch_provenance")
            continue
        for index, patch in enumerate(patches):
            if not isinstance(patch, dict) or patch.get("repair_provider_resolved") != sample["source"]:
                same_source_violations.append(f"{sample['sample_id']}:patch:{index}")
    _record(
        checks,
        blocking,
        "same_source_repair",
        not same_source_violations,
        violating_samples=same_source_violations,
    )

    incomplete_l0_l3 = [
        sample["sample_id"]
        for sample in samples
        if sample["measurement"].get("scoreable") is True and not _has_l0_l3_verdicts(sample["labels"])
    ]
    _record(
        checks,
        blocking,
        "l0_l3_verdicts_complete",
        not incomplete_l0_l3,
        violating_samples=incomplete_l0_l3,
    )

    l4_runs = [sample for sample in samples if sample["l4_open"].get("status") in {"pass", "fail"}]
    non_fir_l4 = [sample["sample_id"] for sample in l4_runs if sample["family_id"] != "fir_filter"]
    _record(
        checks,
        blocking,
        "fir_only_l4",
        not non_fir_l4 and len(l4_runs) <= MAX_L4_RUNS,
        l4_run_count=len(l4_runs),
        max_l4_runs=MAX_L4_RUNS,
        non_fir_samples=non_fir_l4,
    )
    l4_without_l3 = [
        sample["sample_id"]
        for sample in l4_runs
        if not isinstance(sample["labels"].get("checks"), dict)
        or sample["labels"]["checks"].get("l3_synth_pass") is not True
    ]
    _record(
        checks,
        blocking,
        "l4_requires_l3_pass",
        not l4_without_l3,
        violating_samples=l4_without_l3,
    )

    missing_l4_reports: list[str] = []
    for sample in l4_runs:
        report_paths = sample["l4_open"].get("report_paths", [])
        if not isinstance(report_paths, list) or not report_paths:
            missing_l4_reports.append(sample["sample_id"])
            continue
        if any(not (sample["sample_dir"] / str(path)).is_file() for path in report_paths):
            missing_l4_reports.append(sample["sample_id"])
    _record(
        checks,
        blocking,
        "l4_reports_archived",
        not missing_l4_reports,
        violating_samples=missing_l4_reports,
    )

    trusted_violations = _trusted_artifact_violations(samples)
    _record(
        checks,
        blocking,
        "trusted_artifacts_untouched",
        not trusted_violations,
        violations=trusted_violations,
    )

    secret_findings = _secret_findings([run_root, *(sample["sample_dir"] for sample in samples)])
    _record(
        checks,
        blocking,
        "no_secret_material",
        not secret_findings,
        files=secret_findings,
    )

    infrastructure = paired.get("infrastructure_outcomes", {})
    missing_measurement = paired.get("missing_measurement_samples", [])
    unresolved_samples = [
        sample["sample_id"] for sample in samples if sample["measurement"].get("scoreable") is not True
    ]
    infrastructure_ok = (
        isinstance(infrastructure, dict)
        and not infrastructure
        and isinstance(missing_measurement, list)
        and not missing_measurement
        and not unresolved_samples
    )
    _record(
        checks,
        blocking,
        "infrastructure_resolved",
        infrastructure_ok,
        outcomes=infrastructure if isinstance(infrastructure, dict) else {"invalid": 1},
        missing_measurement_samples=missing_measurement,
        unresolved_samples=unresolved_samples,
    )

    paired_agreement = (
        paired.get("episode_count") == len(samples)
        and paired.get("scoreable_episode_count") == scoreable_count
        and paired.get("pair_count") == len(pairs)
        and paired.get("complete_pairs") == complete_pair_count
        and summary.get("paired_results") == paired
    )
    _record(
        checks,
        blocking,
        "paired_summary_agreement",
        paired_agreement,
        paired_episode_count=paired.get("episode_count"),
        actual_episode_count=len(samples),
    )

    return {
        "verdict": "APPROVED" if not blocking else "NOT APPROVED",
        "checks": checks,
        "blocking_findings": blocking,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a frozen SR2FPGA Phase D pilot run.")
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = audit_run(args.run_root)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["verdict"])
    return 0 if result["verdict"] == "APPROVED" else 1


def _read_sample(sample_dir: Path, sample_id: str) -> dict[str, Any]:
    metadata = _read_json(sample_dir / "metadata.json")
    labels = _read_json(sample_dir / "eval" / "labels.json")
    trajectory = _read_json(sample_dir / "eval" / "trajectory.json")
    measurement = trajectory.get("measurement")
    if not isinstance(measurement, dict):
        measurement = {"scoreable": False, "infrastructure_status": "missing_measurement"}
    verification = trajectory.get("verification")
    verification = verification if isinstance(verification, dict) else {}
    l4_open = verification.get("l4_open")
    l4_open = l4_open if isinstance(l4_open, dict) else measurement.get("l4_open", {})
    l4_open = l4_open if isinstance(l4_open, dict) else {"status": "not_run"}
    return {
        "sample_id": sample_id,
        "sample_dir": sample_dir,
        "metadata": metadata,
        "labels": labels,
        "trajectory": trajectory,
        "measurement": measurement,
        "l4_open": l4_open,
        "source": str(metadata.get("source", "")),
        "family_id": str(metadata.get("family_id", "")),
        "paired_requirement_id": str(metadata.get("paired_requirement_id", "")),
        "requirement_sha256": str(metadata.get("requirement_sha256", "")),
        "freeze_fingerprint": str(metadata.get("freeze_fingerprint", "")),
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _group_samples(samples: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for sample in samples:
        groups.setdefault(str(sample.get(key, "")), []).append(sample)
    return groups


def _has_l0_l3_verdicts(labels: dict[str, Any]) -> bool:
    checks = labels.get("checks")
    if not isinstance(checks, dict):
        return False
    return all(isinstance(checks.get(key), bool) for key in (
        "l0_complete",
        "l1_lint_pass",
        "l2_sim_pass",
        "l3_synth_pass",
    ))


def _trusted_artifact_violations(samples: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    for sample in samples:
        patches = sample["trajectory"].get("patches", [])
        if not isinstance(patches, list):
            continue
        for index, patch in enumerate(patches):
            if not isinstance(patch, dict):
                continue
            if patch.get("touched_trusted_artifacts") is True:
                violations.append(f"{sample['sample_id']}:patch:{index}:trusted_flag")
                continue
            files = patch.get("files_touched", [])
            if isinstance(files, list):
                for path in files:
                    normalized = str(path).replace("\\", "/").lower()
                    if any(part in normalized for part in _TRUSTED_PATH_PARTS):
                        violations.append(f"{sample['sample_id']}:patch:{index}:{path}")
    return violations


def _secret_findings(roots: Iterable[Path]) -> list[str]:
    findings: list[str] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                if _file_contains_secret(path):
                    findings.append(str(path))
            except OSError:
                findings.append(f"{path}:unreadable")
                continue
    return sorted(findings)


def _file_contains_secret(path: Path) -> bool:
    overlap = b""
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            searchable = overlap + chunk
            if any(pattern.search(searchable) for pattern in _SECRET_PATTERNS):
                return True
            overlap = searchable[-512:]
    return False


def _record(
    checks: dict[str, dict[str, Any]],
    blocking: list[str],
    name: str,
    passed: bool,
    **details: Any,
) -> None:
    checks[name] = {"pass": bool(passed), **details}
    if not passed:
        blocking.append(name)


if __name__ == "__main__":
    raise SystemExit(main())
