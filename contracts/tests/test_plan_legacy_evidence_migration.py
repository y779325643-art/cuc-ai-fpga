import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = (
    REPO_ROOT
    / "contracts"
    / "tools"
    / "plan_legacy_evidence_migration.py"
)
LEDGER_PATH = (
    REPO_ROOT
    / "reports"
    / "evidence"
    / "task-ledger"
    / "sr2fpga-task-evidence-v0.1.json"
)
PLAN_PATH = (
    REPO_ROOT
    / "reports"
    / "reorganization"
    / "legacy-active-evidence-migration.json"
)
SPEC = importlib.util.spec_from_file_location(
    "plan_legacy_evidence_migration",
    TOOL_PATH,
)
assert SPEC is not None and SPEC.loader is not None
plan_legacy_evidence_migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan_legacy_evidence_migration)


def _ledger(*families: dict) -> dict:
    return {
        "schema_version": "sr2fpga-task-evidence-v0.1",
        "task_families": list(families),
    }


def _family(family_id: str, refs: list[str]) -> dict:
    return {"family_id": family_id, "evidence_refs": refs}


def test_plan_covers_each_unique_reference_once() -> None:
    summary = "tmp/source/runs/run-1/summary.json"
    trajectory = "tmp/source/dataset/sample/eval/trajectory.json"
    mutations = "tmp/source/dataset/sample/oracle_mutations"
    ledger = _ledger(
        _family("first", [summary, trajectory, mutations]),
        _family("second", [summary, trajectory]),
    )

    plan = plan_legacy_evidence_migration.build_plan(
        ledger,
        source_ledger="docs/evidence.json",
    )

    assert plan["reference_occurrence_count"] == 5
    assert plan["unique_reference_count"] == 3
    assert plan["planned_reference_count"] == 3
    assert plan["source_root_count"] == 1
    assert plan["run_count"] == 1
    group = plan["run_groups"][0]
    assert group["run_id"] == "run-1"
    assert group["destination_root"] == (
        "reports/evidence/legacy-runs/run-1"
    )
    records = {
        record["source_reference"]: record
        for record in group["references"]
    }
    assert records[summary]["family_ids"] == ["first", "second"]
    assert records[mutations]["reference_kind"] == "subtree"
    assert records[trajectory]["destination_reference"] == (
        "reports/evidence/legacy-runs/run-1/"
        "dataset/sample/eval/trajectory.json"
    )
    assert all(
        record["migration_status"] == "requires_phase_a_backup"
        for record in records.values()
    )


def test_plan_rejects_unsafe_reference() -> None:
    ledger = _ledger(
        _family(
            "unsafe",
            [
                "tmp/source/runs/run-1/summary.json",
                "tmp/source/../outside.json",
            ],
        )
    )

    with pytest.raises(ValueError, match="unsafe evidence_reference"):
        plan_legacy_evidence_migration.build_plan(
            ledger,
            source_ledger="docs/evidence.json",
        )


def test_plan_requires_one_run_summary_per_source_root() -> None:
    ledger = _ledger(
        _family(
            "missing",
            ["tmp/source/dataset/sample/eval/trajectory.json"],
        )
    )

    with pytest.raises(
        ValueError,
        match="requires exactly one run summary",
    ):
        plan_legacy_evidence_migration.build_plan(
            ledger,
            source_ledger="docs/evidence.json",
        )


def test_plan_output_is_deterministic(tmp_path: Path) -> None:
    ledger = _ledger(
        _family(
            "first",
            [
                "tmp/source/runs/run-1/summary.json",
                "tmp/source/dataset/sample/eval/trajectory.json",
            ],
        )
    )
    plan = plan_legacy_evidence_migration.build_plan(
        ledger,
        source_ledger="docs/evidence.json",
    )
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    plan_legacy_evidence_migration.write_plan(first, plan)
    plan_legacy_evidence_migration.write_plan(second, plan)

    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text(encoding="utf-8")) == plan


def test_empty_plan_is_complete() -> None:
    plan = plan_legacy_evidence_migration.build_plan(
        _ledger(_family("clean", ["reports/evidence/run/summary.json"])),
        source_ledger="docs/evidence.json",
    )

    assert plan["status"] == "complete"
    assert plan["planned_reference_count"] == 0
    assert plan["run_groups"] == []


def test_active_evidence_ledger_requires_no_legacy_migration() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    plan = plan_legacy_evidence_migration.build_plan(
        ledger,
        source_ledger=LEDGER_PATH.relative_to(REPO_ROOT).as_posix(),
    )

    assert plan["source_ledger"] == (
        "reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json"
    )
    assert plan["status"] == "complete"
    assert plan["reference_occurrence_count"] == 0
    assert plan["unique_reference_count"] == 0
    assert plan["planned_reference_count"] == 0
    assert plan["run_groups"] == []


def test_historical_repository_plan_remains_self_consistent() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    assert plan["schema_version"] == (
        "sr2fpga-legacy-active-evidence-migration-v1"
    )
    assert plan["source_ledger"] == "docs/sr2fpga-task-evidence-v0.1.json"
    assert plan["status"] == "complete"
    assert plan["reference_occurrence_count"] == 0
    assert plan["unique_reference_count"] == 0
    assert plan["planned_reference_count"] == 0
    assert plan["run_count"] == len(plan["run_groups"]) == 0
