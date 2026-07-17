import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from LLM.src.sr2fpga_agent.paired_measurement import build_episode_measurement
from LLM.src.sr2fpga_agent.runner import load_runner_config, run_batch
from scripts.audit_phase_d_pilot import audit_run


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_phase_d_mocked_24_episode_run_is_complete_and_auditable(tmp_path: Path) -> None:
    base = load_runner_config(
        REPO_ROOT / "configs" / "current" / "sr2fpga_phase_d_multiteacher_pilot.example.yaml"
    )
    config = replace(
        base,
        dataset_root=tmp_path / "datasets",
        export_root=tmp_path / "exports",
        run_root=tmp_path / "runs",
        env_file=Path(""),
        refresh_exports=False,
    )
    l4_enabled_samples: list[str] = []

    class FakeAgent:
        def __init__(self, dataset_root, *args, **kwargs):
            self.dataset_root = Path(dataset_root)
            self.enable_l4 = bool(kwargs["enable_openxc7_l4"])

        def run_one(self, sample_id, requirement, request, platform, metadata=None):
            sample_dir = self.dataset_root / sample_id
            eval_dir = sample_dir / "eval"
            attempts_dir = sample_dir / "attempts"
            eval_dir.mkdir(parents=True)
            attempts_dir.mkdir(parents=True)
            metadata = dict(metadata or {})
            (sample_dir / "requirement.txt").write_text(requirement.rstrip() + "\n", encoding="utf-8")
            l4 = {
                "status": "pass" if self.enable_l4 else "not_run",
                "skip_reason": None if self.enable_l4 else "not_selected_by_policy",
                "report_paths": [],
            }
            if self.enable_l4:
                l4_enabled_samples.append(sample_id)
                report = sample_dir / "reports" / "openxc7" / "openxc7_nextpnr.log"
                report.parent.mkdir(parents=True)
                report.write_text("Info: Max frequency 100.00 MHz\n", encoding="utf-8")
                l4["report_paths"] = ["reports/openxc7/openxc7_nextpnr.log"]

            attempts = [
                {
                    "attempt_id": 0,
                    "pass_level": "L1",
                    "failure_type": "mock_initial_failure",
                    "repair_eligible": True,
                    "automatic_pass_credit": True,
                },
                {
                    "attempt_id": 1,
                    "pass_level": "L3",
                    "failure_type": "none",
                    "repair_eligible": True,
                    "automatic_pass_credit": True,
                },
            ]
            for attempt in attempts:
                attempt_dir = attempts_dir / f"attempt_{attempt['attempt_id']:03d}"
                attempt_dir.mkdir()
                _write(attempt_dir / "attempt.json", attempt)
            patches = [
                {
                    "patch_id": "mock-patch-1",
                    "repair_provider_resolved": metadata["repair_provider_resolved"],
                    "files_touched": ["rtl/core.v"],
                    "touched_trusted_artifacts": False,
                    "regressions": [],
                }
            ]
            measurement = build_episode_measurement(attempts=attempts, patches=patches, l4_open=l4)
            labels = {
                "pass_level": "L4" if self.enable_l4 else "L3",
                "l4_open_status": l4["status"],
                "l4_open_skip_reason": l4["skip_reason"],
                "checks": {
                    "l0_complete": True,
                    "l1_lint_pass": True,
                    "l2_sim_pass": True,
                    "l3_synth_pass": True,
                },
            }
            _write(sample_dir / "metadata.json", metadata)
            _write(eval_dir / "labels.json", labels)
            _write(
                eval_dir / "trajectory.json",
                {
                    "attempts": attempts,
                    "patches": patches,
                    "measurement": measurement,
                    "verification": {"l4_open": l4},
                },
            )
            return {"sample_dir": str(sample_dir), "pass_level": labels["pass_level"]}

    run_id = "phase-d-mocked-24"
    with (
        patch("LLM.src.sr2fpga_agent.runner.DataGenerationAgent", FakeAgent),
        patch("LLM.src.sr2fpga_agent.runner._project_generator_for_sample", return_value=object()),
        patch("LLM.src.sr2fpga_agent.runner._repairer_for_sample", return_value=object()),
        patch("LLM.src.sr2fpga_agent.runner._measurement_tool_versions", return_value={}),
    ):
        summary = run_batch(config, run_id=run_id, resume=False)

    run_root = config.run_root / run_id
    state = _read(run_root / "run_state.json")
    paired = _read(run_root / "paired_results.json")
    freeze = _read(run_root / "measurement_freeze.json")

    assert len(state["completed_samples"]) == 24
    assert freeze["sample_count"] == 24
    assert paired["episode_count"] == 24
    assert paired["scoreable_episode_count"] == 24
    assert paired["complete_pairs"] == 6
    assert set(paired["by_source"]) == {"claude", "gpt", "qwen", "deepseek"}
    assert summary["paired_results"] == paired
    assert len(l4_enabled_samples) == 4
    assert all(_read(config.dataset_root / sample_id / "metadata.json")["family_id"] == "fir_filter" for sample_id in l4_enabled_samples)
    for sample_id in state["completed_samples"]:
        sample_dir = config.dataset_root / sample_id
        assert (sample_dir / "attempts" / "attempt_000" / "attempt.json").is_file()
        metadata = _read(sample_dir / "metadata.json")
        assert metadata["repair_provider_policy"] == "same_as_source"
        assert metadata["repair_provider_resolved"] == metadata["source"]
        trajectory = _read(sample_dir / "eval" / "trajectory.json")
        assert trajectory["patches"][0]["repair_provider_resolved"] == metadata["source"]

    audit = audit_run(run_root)
    assert audit["verdict"] == "APPROVED", audit


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
