"""Analyze frozen Phase D failures and replay generated HIS through current H2."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from LLM.src.sr2fpga_agent.his_validation import validate_system_his_h_stages
from LLM.src.sr2fpga_agent.models import GeneratedProject, ProjectRequest


def analyze_dataset(dataset_root: Path) -> dict[str, Any]:
    dataset_root = dataset_root.resolve()
    samples = sorted(path for path in dataset_root.glob("sample_*") if path.is_dir())
    pass_levels: Counter[str] = Counter()
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    generation_categories: Counter[str] = Counter()
    before_status: Counter[str] = Counter()
    after_status: Counter[str] = Counter()
    before_diagnostics: Counter[str] = Counter()
    after_diagnostics: Counter[str] = Counter()
    before_affected: dict[str, set[str]] = defaultdict(set)
    after_affected: dict[str, set[str]] = defaultdict(set)
    changed_to_pass: list[str] = []
    replay_errors: dict[str, str] = {}
    records: list[dict[str, Any]] = []

    for sample in samples:
        metadata = _read_json(sample / "metadata.json")
        trajectory = _read_json(sample / "eval" / "trajectory.json")
        pass_level = str(trajectory.get("measurement", {}).get("final", {}).get("pass_level", "UNKNOWN"))
        source = str(metadata.get("source", "unknown"))
        family = str(metadata.get("family_id", metadata.get("task_type", "unknown")))
        pass_levels[pass_level] += 1
        by_source[source][pass_level] += 1
        by_family[family][pass_level] += 1
        record: dict[str, Any] = {
            "sample_id": sample.name,
            "source": source,
            "family_id": family,
            "pass_level": pass_level,
        }

        if pass_level == "GEN_FAIL":
            diagnosis = _read_json(sample / "attempts" / "attempt_000" / "diagnosis.json")
            root_cause = str(diagnosis.get("root_cause", ""))
            category = _generation_failure_category(root_cause)
            generation_categories[category] += 1
            record.update({"generation_category": category, "root_cause": root_cause})
        elif pass_level == "H2_FAIL":
            old_h2 = trajectory.get("his_validation", {}).get("h2", {})
            old_status = str(old_h2.get("status", "not_run"))
            old_diagnostics = [str(item) for item in old_h2.get("diagnostics", [])]
            before_status[old_status] += 1
            _count_diagnostics(sample.name, old_diagnostics, before_diagnostics, before_affected)
            try:
                new_h2 = _replay_h2(sample, metadata)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                replay_errors[sample.name] = str(exc)
                new_h2 = {"status": "replay_error", "diagnostics": [str(exc)]}
            new_status = str(new_h2.get("status", "not_run"))
            new_diagnostics = [str(item) for item in new_h2.get("diagnostics", [])]
            after_status[new_status] += 1
            _count_diagnostics(sample.name, new_diagnostics, after_diagnostics, after_affected)
            if old_status == "fail" and new_status == "pass":
                changed_to_pass.append(sample.name)
            record.update(
                {
                    "h2_before": {"status": old_status, "diagnostics": old_diagnostics},
                    "h2_after": {"status": new_status, "diagnostics": new_diagnostics},
                }
            )
        records.append(record)

    return {
        "schema_version": "sr2fpga-phase-d-h2-analysis-v1",
        "dataset_root": str(dataset_root),
        "total_samples": len(samples),
        "pass_level_distribution": _counter_dict(pass_levels),
        "by_source": _nested_counter_dict(by_source),
        "by_family": _nested_counter_dict(by_family),
        "generation_failures": {
            "total": sum(generation_categories.values()),
            "categories": _counter_dict(generation_categories),
        },
        "h2_replay": {
            "candidates": sum(before_status.values()),
            "before_status": _counter_dict(before_status),
            "after_status": _counter_dict(after_status),
            "changed_to_pass": sorted(changed_to_pass),
            "replay_errors": dict(sorted(replay_errors.items())),
            "diagnostic_occurrences_before": _counter_dict(before_diagnostics),
            "diagnostic_occurrences_after": _counter_dict(after_diagnostics),
            "affected_samples_before": _set_count_dict(before_affected),
            "affected_samples_after": _set_count_dict(after_affected),
        },
        "samples": records,
    }


def _replay_h2(sample: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    project_root = sample / "final" / "generated_project"
    his_path = project_root / "system_his.json"
    if not his_path.is_file():
        raise ValueError("generated project has no system_his.json")
    request = ProjectRequest(
        task_type=str(metadata.get("task_type", "")),
        width=int(metadata.get("width", 0)),
        project_name=sample.name,
        description=(sample / "requirement.txt").read_text(encoding="utf-8").strip(),
    )
    project = GeneratedProject(
        project_name=sample.name,
        files={"system_his.json": his_path.read_text(encoding="utf-8")},
    )
    return validate_system_his_h_stages(request, project).get("h2", {})


def _generation_failure_category(root_cause: str) -> str:
    text = root_cause.lower()
    if "not valid json" in text:
        return "invalid_json"
    if "behavior file" in text and "behavior_hole" in text:
        return "behavior_hole_merge"
    if "req2his fidelity failed" in text:
        return "req_his_fidelity"
    if "his2project rtl failed" in text:
        return "rtl_his_cross_check"
    if "system-his v1.2 failed validation" in text:
        return "his_contract_validation"
    return "other_generation_failure"


def _diagnostic_category(diagnostic: str) -> str:
    if "unsupported semantic_kind" in diagnostic:
        return "unsupported_semantic_kind"
    if "unsupported protocol" in diagnostic:
        return "unsupported_protocol"
    if "unsupported scenario" in diagnostic:
        return "unsupported_scenario"
    if "scenario object requires" in diagnostic:
        return "missing_scenario_identifier"
    if "unsupported testbench" in diagnostic:
        return "unsupported_testbench"
    return "other_h2_diagnostic"


def _count_diagnostics(
    sample_id: str,
    diagnostics: list[str],
    counts: Counter[str],
    affected: dict[str, set[str]],
) -> None:
    for diagnostic in diagnostics:
        category = _diagnostic_category(diagnostic)
        counts[category] += 1
        affected[category].add(sample_id)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _nested_counter_dict(values: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: _counter_dict(values[key]) for key in sorted(values)}


def _set_count_dict(values: dict[str, set[str]]) -> dict[str, int]:
    return {key: len(values[key]) for key in sorted(values)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dataset_root = args.dataset_root.resolve()
    report = analyze_dataset(dataset_root)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = args.output.resolve()
        if output == dataset_root or dataset_root in output.parents:
            raise SystemExit("analysis output must be outside the frozen dataset root")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
