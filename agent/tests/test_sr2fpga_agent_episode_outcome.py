from __future__ import annotations

import json
from pathlib import Path

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.episode_outcome import (
    EpisodeOutcomeError,
    project_development_public_evaluation,
)
from sr2fpga_agent.paired_measurement import build_episode_measurement


def _labels(*, public_l2: str = "pass", skip_reason: str | None = None) -> dict:
    return {
        "pass_level": "L3",
        "failure_origin": None,
        "automatic_pass_credit": True,
        "l2_sim_status": public_l2,
        "l2_sim_skip_reason": skip_reason,
        "checks": {
            "l0_complete": True,
            "l1_lint_pass": True,
            "l2_sim_pass": public_l2 == "pass",
            "l3_synth_pass": True,
        },
    }


def _patch() -> dict:
    return {
        "diagnosis_id": "d001",
        "files_touched": ["rtl/top.v"],
        "allowed_edit_regions_respected": True,
        "touched_trusted_artifacts": False,
        "status": "valid",
        "regressions": [],
    }


def _write_legacy(
    sample_dir: Path,
    *,
    episode_id: str,
    labels: dict,
    attempts: list[dict],
    patches: list[dict],
    measurement: dict,
) -> None:
    eval_dir = sample_dir / "eval"
    eval_dir.mkdir(parents=True)
    (eval_dir / "labels.json").write_text(
        json.dumps(labels, sort_keys=True), encoding="utf-8"
    )
    (eval_dir / "trajectory.json").write_text(
        json.dumps(
            {
                "sample_id": episode_id,
                "attempt_measurements": attempts,
                "patches": patches,
                "measurement": measurement,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_public_projection_rebuilds_valid_repair_transition(tmp_path: Path) -> None:
    attempts = [
        {
            "attempt_id": 0,
            "pass_level": "L1",
            "failure_type": "simulation_mismatch",
            "repair_scope": "project",
            "repair_attempted": True,
            "repair_call_status": "succeeded",
        },
        {"attempt_id": 1, "pass_level": "L3", "failure_type": "none"},
    ]
    patches = [_patch()]
    measurement = build_episode_measurement(attempts=attempts, patches=patches)
    sample_dir = tmp_path / "sample"
    _write_legacy(
        sample_dir,
        episode_id="episode-repair",
        labels=_labels(),
        attempts=attempts,
        patches=patches,
        measurement=measurement,
    )

    payload, reference = project_development_public_evaluation(
        ArtifactStore(tmp_path / "store"),
        sample_dir=sample_dir,
        episode_id="episode-repair",
        method_condition="M1",
        analysis_population="excluded",
    )

    assert payload["repair"] == {
        "reconciliation_status": "complete",
        "calls_attempted": 1,
        "transitions": 1,
        "successes": 1,
        "diagnosis_count": 1,
        "valid_patch_count": 1,
        "rerun_count": 1,
        "by_scope": {
            "system_his": {"calls_attempted": 0, "transitions": 0},
            "project": {"calls_attempted": 1, "transitions": 1},
        },
        "issues": [],
    }
    assert payload["missingness"]["classification"] == "scoreable_public_record"
    assert payload["vpp_l3"] is None
    assert reference.key == "public-evaluations/episode-repair/M1"


def test_public_projection_rejects_tampered_repair_measurement(tmp_path: Path) -> None:
    attempts = [
        {
            "attempt_id": 0,
            "pass_level": "L1",
            "failure_type": "simulation_mismatch",
            "repair_scope": "project",
            "repair_attempted": True,
            "repair_call_status": "succeeded",
        },
        {"attempt_id": 1, "pass_level": "L3", "failure_type": "none"},
    ]
    patches = [_patch()]
    measurement = build_episode_measurement(attempts=attempts, patches=patches)
    measurement["repair_transitions"] = 0
    sample_dir = tmp_path / "sample"
    _write_legacy(
        sample_dir,
        episode_id="episode-tampered-repair",
        labels=_labels(),
        attempts=attempts,
        patches=patches,
        measurement=measurement,
    )

    with pytest.raises(
        EpisodeOutcomeError, match="repair measurement does not rebuild"
    ):
        project_development_public_evaluation(
            ArtifactStore(tmp_path / "store"),
            sample_dir=sample_dir,
            episode_id="episode-tampered-repair",
            method_condition="M1",
            analysis_population="excluded",
        )


def test_public_projection_retains_infrastructure_not_run(tmp_path: Path) -> None:
    attempts = [
        {
            "attempt_id": 0,
            "pass_level": "L1",
            "failure_type": "tool_missing",
            "automatic_pass_credit": False,
            "infrastructure_reason": "public_tool_missing",
            "repair_eligible": False,
            "repair_skip_reason": "infrastructure_failure",
        }
    ]
    measurement = build_episode_measurement(attempts=attempts, patches=[])
    sample_dir = tmp_path / "sample"
    _write_legacy(
        sample_dir,
        episode_id="episode-infra",
        labels=_labels(public_l2="not_run", skip_reason="tool_missing"),
        attempts=attempts,
        patches=[],
        measurement=measurement,
    )

    payload, _ = project_development_public_evaluation(
        ArtifactStore(tmp_path / "store"),
        sample_dir=sample_dir,
        episode_id="episode-infra",
        method_condition="M0",
        analysis_population="excluded",
    )

    assert payload["missingness"] == {
        "classification": "infrastructure_unscorable",
        "reason": "public_tool_missing",
        "retained": True,
        "replacement_allowed": False,
    }
    assert payload["stage_outcomes"]["public_l2"] == {
        "status": "not_run",
        "reason": "tool_missing",
    }
