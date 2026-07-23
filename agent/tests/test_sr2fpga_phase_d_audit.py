import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sr2fpga_agent.measurement_freeze import freeze_fingerprint
from sr2fpga_agent.paired_measurement import collect_paired_results
from agent.scripts.audit_phase_d_pilot import audit_run


SOURCES = ("claude", "gpt", "qwen", "deepseek")
FAMILIES = (
    "sync_fifo",
    "valid_ready_stream_accumulator",
    "stream_fork_join",
    "fir_filter",
    "sobel_threshold",
    "qtable_update_core",
)


def test_phase_d_audit_script_runs_directly_from_repo_root(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    run_root = _valid_run(tmp_path)
    output_path = run_root / "direct-audit.json"

    result = subprocess.run(
        [
            sys.executable,
            "agent/scripts/audit_phase_d_pilot.py",
            "--run-root",
            str(run_root),
            "--output",
            str(output_path),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "APPROVED"
    assert _read(output_path)["verdict"] == "APPROVED"


def test_phase_d_audit_approves_complete_synthetic_run(tmp_path: Path) -> None:
    run_root = _valid_run(tmp_path)

    result = audit_run(run_root)

    assert result["verdict"] == "APPROVED"
    assert result["blocking_findings"] == []
    assert all(check["pass"] for check in result["checks"].values())


@pytest.mark.parametrize(
    ("mutation", "expected_check"),
    (
        ("missing_episode", "scoreable_episode_count"),
        ("duplicate_source", "complete_pairs"),
        ("requirement_hash_mismatch", "same_requirement_per_pair"),
        ("requirement_file_mismatch", "frozen_sample_identity"),
        ("freeze_entry_mismatch", "frozen_sample_identity"),
        ("freeze_mismatch", "freeze_consistency"),
        ("repair_provider_mismatch", "same_source_repair"),
        ("non_fir_l4", "fir_only_l4"),
        ("l4_without_l3", "l4_requires_l3_pass"),
        ("too_many_l4", "fir_only_l4"),
        ("trusted_artifact", "trusted_artifacts_untouched"),
        ("secret_material", "no_secret_material"),
        ("secret_extensionless", "no_secret_material"),
        ("infrastructure", "infrastructure_resolved"),
        ("missing_l4_report", "l4_reports_archived"),
    ),
)
def test_phase_d_audit_rejects_integrity_violation(
    tmp_path: Path,
    mutation: str,
    expected_check: str,
) -> None:
    run_root = _valid_run(tmp_path)
    dataset_root = Path(json.loads((run_root / "config.json").read_text(encoding="utf-8"))["dataset_root"])
    completed = json.loads((run_root / "run_state.json").read_text(encoding="utf-8"))["completed_samples"]

    if mutation == "missing_episode":
        state = _read(run_root / "run_state.json")
        state["completed_samples"] = state["completed_samples"][:-1]
        _write(run_root / "run_state.json", state)
    elif mutation == "duplicate_source":
        first = _read(dataset_root / completed[0] / "metadata.json")
        second_path = dataset_root / completed[1] / "metadata.json"
        second = _read(second_path)
        second["source"] = first["source"]
        _write(second_path, second)
    elif mutation == "requirement_hash_mismatch":
        metadata_path = dataset_root / completed[0] / "metadata.json"
        metadata = _read(metadata_path)
        metadata["requirement_sha256"] = "9" * 64
        _write(metadata_path, metadata)
    elif mutation == "requirement_file_mismatch":
        (dataset_root / completed[0] / "requirement.txt").write_text(
            "A different requirement.\n",
            encoding="utf-8",
        )
    elif mutation == "freeze_entry_mismatch":
        freeze_path = run_root / "measurement_freeze.json"
        freeze = _read(freeze_path)
        freeze["samples"][0]["source"] = "different-source"
        freeze["freeze_fingerprint"] = freeze_fingerprint(freeze)
        _write(freeze_path, freeze)
        for sample_id in completed:
            metadata_path = dataset_root / sample_id / "metadata.json"
            metadata = _read(metadata_path)
            metadata["freeze_fingerprint"] = freeze["freeze_fingerprint"]
            _write(metadata_path, metadata)
        summary_path = run_root / "summary.json"
        summary = _read(summary_path)
        summary["freeze_fingerprint"] = freeze["freeze_fingerprint"]
        _write(summary_path, summary)
    elif mutation == "freeze_mismatch":
        metadata_path = dataset_root / completed[0] / "metadata.json"
        metadata = _read(metadata_path)
        metadata["freeze_fingerprint"] = "0" * 64
        _write(metadata_path, metadata)
    elif mutation == "repair_provider_mismatch":
        trajectory_path = dataset_root / completed[0] / "eval" / "trajectory.json"
        trajectory = _read(trajectory_path)
        trajectory["measurement"]["repair_attempts_used"] = 1
        trajectory["patches"] = [{"repair_provider_resolved": "different-source"}]
        _write(trajectory_path, trajectory)
    elif mutation == "non_fir_l4":
        _set_l4(dataset_root / completed[0], "pass", report=True)
    elif mutation == "l4_without_l3":
        fir_sample = next(
            sample_id
            for sample_id in completed
            if _read(dataset_root / sample_id / "metadata.json")["family_id"] == "fir_filter"
        )
        _set_l4(dataset_root / fir_sample, "pass", report=True)
        labels_path = dataset_root / fir_sample / "eval" / "labels.json"
        labels = _read(labels_path)
        labels["checks"]["l3_synth_pass"] = False
        _write(labels_path, labels)
    elif mutation == "too_many_l4":
        _set_l4(dataset_root / completed[0], "pass", report=True)
    elif mutation == "trusted_artifact":
        trajectory_path = dataset_root / completed[0] / "eval" / "trajectory.json"
        trajectory = _read(trajectory_path)
        trajectory["patches"] = [{"touched_trusted_artifacts": True}]
        _write(trajectory_path, trajectory)
    elif mutation == "secret_material":
        (run_root / "leaked.txt").write_text("Authorization: Bearer sk-live-secret-material-123456\n", encoding="utf-8")
    elif mutation == "secret_extensionless":
        (run_root / "credential_blob").write_text("api_key=secret-material\n", encoding="utf-8")
    elif mutation == "infrastructure":
        paired = _read(run_root / "paired_results.json")
        paired["infrastructure_outcomes"] = {"provider_infrastructure_failure": 1}
        _write(run_root / "paired_results.json", paired)
    elif mutation == "missing_l4_report":
        fir_sample = next(
            sample_id
            for sample_id in completed
            if _read(dataset_root / sample_id / "metadata.json")["family_id"] == "fir_filter"
        )
        trajectory_path = dataset_root / fir_sample / "eval" / "trajectory.json"
        trajectory = _read(trajectory_path)
        trajectory["verification"] = {
            "l4_open": {"status": "pass", "report_paths": ["reports/missing.log"]}
        }
        _write(trajectory_path, trajectory)

    result = audit_run(run_root)

    assert result["verdict"] == "NOT APPROVED"
    assert result["checks"][expected_check]["pass"] is False
    assert result["blocking_findings"]


def _valid_run(tmp_path: Path) -> Path:
    run_root = tmp_path / "run"
    dataset_root = tmp_path / "dataset"
    run_root.mkdir()
    sample_ids: list[str] = []
    freeze_samples: list[dict[str, str]] = []
    for family_index, family_id in enumerate(FAMILIES):
        requirement = f"Phase D requirement for {family_id}."
        requirement_hash = hashlib.sha256(requirement.encode("utf-8")).hexdigest()
        paired_id = f"{family_id}:{requirement_hash[:16]}"
        for source in SOURCES:
            sample_id = f"phase-d-{family_id}-{source}"
            sample_ids.append(sample_id)
            freeze_samples.append(
                {
                    "sample_id": sample_id,
                    "source": source,
                    "family_id": family_id,
                    "paired_requirement_id": paired_id,
                    "requirement_sha256": requirement_hash,
                }
            )
            _write_sample(
                dataset_root,
                sample_id=sample_id,
                source=source,
                family_id=family_id,
                paired_id=paired_id,
                requirement=requirement,
                requirement_hash=requirement_hash,
                l4_status="pass" if family_id == "fir_filter" else "not_run",
            )

    freeze = {
        "schema_version": "sr2fpga-phase-d-freeze-v1",
        "run_id": "phase-d-synthetic",
        "config_fingerprint": "c" * 64,
        "sample_count": 24,
        "samples": freeze_samples,
        "sources": [{"alias": source, "model": source} for source in SOURCES],
        "max_attempts": 3,
        "timeouts": {},
        "tool_versions": {},
        "l4_family_ids": ["fir_filter"],
    }
    freeze["freeze_fingerprint"] = freeze_fingerprint(freeze)
    for sample_id in sample_ids:
        metadata_path = dataset_root / sample_id / "metadata.json"
        metadata = _read(metadata_path)
        metadata["freeze_fingerprint"] = freeze["freeze_fingerprint"]
        _write(metadata_path, metadata)

    paired = collect_paired_results(dataset_root, sample_ids)
    paired["missing_measurement_samples"] = []
    _write(run_root / "measurement_freeze.json", freeze)
    _write(run_root / "paired_results.json", paired)
    _write(run_root / "summary.json", {"paired_results": paired, "freeze_fingerprint": freeze["freeze_fingerprint"]})
    _write(run_root / "config.json", {"dataset_root": str(dataset_root)})
    _write(run_root / "run_state.json", {"completed_samples": sample_ids})
    return run_root


def _write_sample(
    root: Path,
    *,
    sample_id: str,
    source: str,
    family_id: str,
    paired_id: str,
    requirement: str,
    requirement_hash: str,
    l4_status: str,
) -> None:
    sample_dir = root / sample_id
    (sample_dir / "eval").mkdir(parents=True)
    (sample_dir / "requirement.txt").write_text(requirement + "\n", encoding="utf-8")
    _write(
        sample_dir / "metadata.json",
        {
            "source": source,
            "family_id": family_id,
            "paired_requirement_id": paired_id,
            "requirement_sha256": requirement_hash,
            "repair_provider_policy": "same_as_source",
            "repair_provider_resolved": source,
        },
    )
    _write(
        sample_dir / "eval" / "labels.json",
        {
            "pass_level": "L4" if l4_status == "pass" else "L3",
            "automatic_pass_credit": True,
            "l4_open_status": l4_status,
            "checks": {
                "l0_complete": True,
                "l1_lint_pass": True,
                "l2_sim_pass": True,
                "l3_synth_pass": True,
            },
        },
    )
    report_paths: list[str] = []
    if l4_status == "pass":
        report_path = "attempts/attempt_000/generated_project/reports/openxc7_nextpnr.log"
        report_target = sample_dir / report_path
        report_target.parent.mkdir(parents=True)
        report_target.write_text("SLICE_LUTX: 12\nMax frequency: 123.45 MHz\n", encoding="utf-8")
        report_paths.append(report_path)
    _write(
        sample_dir / "eval" / "trajectory.json",
        {
            "sample_id": sample_id,
            "measurement": {
                "initial": {"attempt_id": 0, "pass_level": "L3", "automatic_pass_credit": True},
                "final": {"attempt_id": 0, "pass_level": "L3", "automatic_pass_credit": True},
                "repair_attempts_used": 0,
                "repair_success": False,
                "regressions": [],
                "scoreable": True,
                "infrastructure_status": "scoreable",
                "l4_open": {"status": l4_status, "skip_reason": None if l4_status == "pass" else "not_selected_by_policy"},
            },
            "verification": {
                "l4_open": {
                    "status": l4_status,
                    "skip_reason": None if l4_status == "pass" else "not_selected_by_policy",
                    "report_paths": report_paths,
                }
            },
            "patches": [],
        },
    )


def _set_l4(sample_dir: Path, status: str, *, report: bool) -> None:
    labels_path = sample_dir / "eval" / "labels.json"
    labels = _read(labels_path)
    labels["l4_open_status"] = status
    _write(labels_path, labels)
    trajectory_path = sample_dir / "eval" / "trajectory.json"
    trajectory = _read(trajectory_path)
    report_paths: list[str] = []
    if report:
        path = "attempts/attempt_000/generated_project/reports/openxc7_nextpnr.log"
        target = sample_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("SLICE_LUTX: 1\nMax frequency: 100 MHz\n", encoding="utf-8")
        report_paths.append(path)
    trajectory["measurement"]["l4_open"] = {"status": status, "skip_reason": None}
    trajectory["verification"]["l4_open"] = {"status": status, "report_paths": report_paths}
    _write(trajectory_path, trajectory)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
