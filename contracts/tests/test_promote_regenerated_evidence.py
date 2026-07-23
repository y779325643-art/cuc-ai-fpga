import json
from pathlib import Path

import pytest

from contracts.tools.promote_regenerated_evidence import (
    apply_promotion,
    build_promotion_preview,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _fixture(
    tmp_path: Path,
    *,
    strip_prefix: str = "",
    legacy_sample_id: str = "sample",
    current_sample_id: str = "sample",
) -> tuple[Path, Path, Path, Path]:
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    candidate_root = repository / "artifacts" / "agent" / "candidates" / "candidate"
    run_root = repository / "artifacts" / "agent" / "runs" / "candidate" / "run-1"
    sample_root = candidate_root / "dataset" / current_sample_id

    _write_json(
        run_root / "summary.json",
        {
            "run_id": "run-1",
            "buckets": {"success_l3": [current_sample_id]},
        },
    )
    _write_json(
        sample_root / "metadata.json",
        {"sample_id": current_sample_id, "family_id": "family"},
    )
    _write_json(
        sample_root / "eval" / "trajectory.json",
        {
            "sample_id": current_sample_id,
            "project_dir": str(repository / "private" / "project"),
        },
    )
    _write_json(
        sample_root / "eval" / "labels.json",
        {"pass_level": "L3", "highest_official_level": "L3"},
    )
    _write_json(sample_root / "eval" / "measured_qor.json", {})
    _write_json(sample_root / "eval" / "tool_versions.json", {})
    _write_json(
        sample_root / "attempts" / "attempt_000" / "eval" / "sim_compile.json",
        {"stage": "sim_compile", "status": "passed"},
    )
    mutation_root = sample_root / "oracle_mutations" / "broken" / "eval"
    _write_json(
        mutation_root / "sim_compile.json",
        {"stage": "sim_compile", "status": "passed"},
    )
    _write_json(
        mutation_root / "sim_run.json",
        {
            "stage": "sim_run",
            "status": "failed",
            "stdout": "TEST_FAIL",
        },
    )
    (mutation_root.parent / "sim.out").write_bytes(b"binary")
    (mutation_root.parent / "hidden.memh").write_text("00\n", encoding="ascii")

    plan_path = repository / "reports" / "reorganization" / "plan.json"
    legacy_prefix = f"{strip_prefix}dataset/{legacy_sample_id}"
    legacy_run_prefix = f"{strip_prefix}runs/run-1"
    _write_json(
        plan_path,
        {
            "schema_version": "sr2fpga-legacy-active-evidence-migration-v1",
            "planned_reference_count": 3,
            "reference_occurrence_count": 3,
            "run_groups": [
                {
                    "run_id": "run-1",
                    "source_root": "tmp/legacy",
                    "destination_root": "reports/evidence/legacy-runs/run-1",
                    "references": [
                        {
                            "source_reference": (
                                f"tmp/legacy/{legacy_run_prefix}/summary.json"
                            ),
                            "source_relative_path": (
                                f"{legacy_run_prefix}/summary.json"
                            ),
                            "reference_kind": "file",
                        },
                        {
                            "source_reference": (
                                f"tmp/legacy/{legacy_prefix}/eval/trajectory.json"
                            ),
                            "source_relative_path": (
                                f"{legacy_prefix}/eval/trajectory.json"
                            ),
                            "reference_kind": "file",
                        },
                        {
                            "source_reference": (
                                f"tmp/legacy/{legacy_prefix}/oracle_mutations"
                            ),
                            "source_relative_path": (
                                f"{legacy_prefix}/oracle_mutations"
                            ),
                            "reference_kind": "subtree",
                        },
                    ],
                }
            ],
        },
    )
    source_map_path = (
        repository / "reports" / "reorganization" / "sources.json"
    )
    replacements = (
        [
            {
                "from": legacy_sample_id,
                "to": current_sample_id,
            }
        ]
        if legacy_sample_id != current_sample_id
        else []
    )
    _write_json(
        source_map_path,
        {
            "schema_version": "sr2fpga-regenerated-evidence-sources-v1",
            "groups": [
                {
                    "run_id": "run-1",
                    "legacy_source_root": "tmp/legacy",
                    "candidate_root": candidate_root.relative_to(repository).as_posix(),
                    "run_root": run_root.relative_to(repository).as_posix(),
                    "strip_prefix": strip_prefix,
                    "replacements": replacements,
                }
            ],
        },
    )
    ledger_path = repository / "docs" / "evidence.json"
    _write_json(
        ledger_path,
        {
            "schema_version": "test",
            "task_families": [
                {
                    "family_id": "family",
                    "evidence_refs": [
                        f"tmp/legacy/{legacy_run_prefix}/summary.json",
                        f"tmp/legacy/{legacy_prefix}/eval/trajectory.json",
                        f"tmp/legacy/{legacy_prefix}/oracle_mutations",
                    ],
                }
            ],
        },
    )
    return repository, plan_path, source_map_path, ledger_path


def test_preview_sanitizes_paths_and_excludes_hidden_vectors_and_binaries(
    tmp_path: Path,
) -> None:
    repository, plan_path, source_map_path, ledger_path = _fixture(tmp_path)

    preview = build_promotion_preview(
        repository,
        plan_path=plan_path,
        source_map_path=source_map_path,
        ledger_path=ledger_path,
    )

    assert preview["status"] == "ready"
    assert preview["reference_count"] == 3
    assert preview["reference_occurrence_count"] == 3
    assert preview["blocked_secret_paths"] == []
    assert preview["blocked_private_path_files"] == []
    assert preview["excluded_file_count"] == 2
    assert all(
        not record["destination_path"].endswith((".memh", "sim.out"))
        for record in preview["files"]
    )
    trajectory = next(
        record
        for record in preview["files"]
        if record["destination_path"].endswith("/eval/trajectory.json")
    )
    assert "redact_absolute_paths" in trajectory["transformations"]
    assert not (repository / "reports" / "evidence").exists()


def test_apply_copies_curated_files_and_rewrites_ledger_references(
    tmp_path: Path,
) -> None:
    repository, plan_path, source_map_path, ledger_path = _fixture(tmp_path)
    preview = build_promotion_preview(
        repository,
        plan_path=plan_path,
        source_map_path=source_map_path,
        ledger_path=ledger_path,
    )

    result = apply_promotion(repository, preview)

    assert result["status"] == "pass"
    assert result["rewritten_reference_occurrence_count"] == 3
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    references = ledger["task_families"][0]["evidence_refs"]
    assert all(reference.startswith("reports/evidence/legacy-runs/run-1/") for reference in references)
    curated_trajectory = (
        repository
        / "reports"
        / "evidence"
        / "legacy-runs"
        / "run-1"
        / "dataset"
        / "sample"
        / "eval"
        / "trajectory.json"
    )
    text = curated_trajectory.read_text(encoding="utf-8")
    assert "<REPOSITORY_ROOT>" in text
    assert str(repository) not in text
    assert not any(
        path.suffix == ".memh" or path.name == "sim.out"
        for path in (repository / "reports" / "evidence").rglob("*")
    )


def test_preview_applies_phase_b_style_prefix_and_sample_replacement(
    tmp_path: Path,
) -> None:
    repository, plan_path, source_map_path, ledger_path = _fixture(
        tmp_path,
        strip_prefix="v4/",
        legacy_sample_id="sample_v4_uart",
        current_sample_id="sample_uart",
    )

    preview = build_promotion_preview(
        repository,
        plan_path=plan_path,
        source_map_path=source_map_path,
        ledger_path=ledger_path,
    )

    mapped = {
        record["source_reference"]: record["destination_reference"]
        for record in preview["reference_map"]
    }
    assert mapped[
        "tmp/legacy/v4/dataset/sample_v4_uart/eval/trajectory.json"
    ].endswith("/dataset/sample_uart/eval/trajectory.json")


def test_secret_content_blocks_promotion(tmp_path: Path) -> None:
    repository, plan_path, source_map_path, ledger_path = _fixture(tmp_path)
    summary = (
        repository
        / "artifacts"
        / "agent"
        / "runs"
        / "candidate"
        / "run-1"
        / "summary.json"
    )
    _write_json(
        summary,
        {
            "run_id": "run-1",
            "api_key": "sk-123456789012345678901234",
        },
    )

    preview = build_promotion_preview(
        repository,
        plan_path=plan_path,
        source_map_path=source_map_path,
        ledger_path=ledger_path,
    )

    assert preview["status"] == "blocked_review"
    assert preview["blocked_secret_paths"]
    with pytest.raises(ValueError, match="not ready"):
        apply_promotion(repository, preview)


def test_apply_rejects_source_changed_after_preview(tmp_path: Path) -> None:
    repository, plan_path, source_map_path, ledger_path = _fixture(tmp_path)
    preview = build_promotion_preview(
        repository,
        plan_path=plan_path,
        source_map_path=source_map_path,
        ledger_path=ledger_path,
    )
    summary = (
        repository
        / "artifacts"
        / "agent"
        / "runs"
        / "candidate"
        / "run-1"
        / "summary.json"
    )
    _write_json(summary, {"run_id": "run-1", "changed": True})

    with pytest.raises(ValueError, match="source changed after preview"):
        apply_promotion(repository, preview)
