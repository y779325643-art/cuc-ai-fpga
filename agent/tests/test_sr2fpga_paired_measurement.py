import json
from pathlib import Path

import pytest

from sr2fpga_agent.agent import _raw_tool_pass_level
from sr2fpga_agent.models import ToolResult
from sr2fpga_agent.paired_measurement import (
    build_episode_measurement,
    collect_paired_results,
)


def _result(stage: str, status: str = "passed") -> ToolResult:
    return ToolResult(
        stage=stage,
        command=[stage],
        status=status,
        exit_code=0 if status == "passed" else 1,
        stdout="",
        stderr="",
        duration_seconds=0.1,
    )


def test_raw_tool_pass_level_stops_at_each_verification_boundary() -> None:
    assert _raw_tool_pass_level({}, None) == "L0"
    assert _raw_tool_pass_level({"l0_consistency": _result("l0_consistency", "failed")}, None) == "L0_FAIL"
    assert _raw_tool_pass_level({"lint": _result("lint")}, None) == "L1"
    assert _raw_tool_pass_level(
        {
            "lint": _result("lint"),
            "sim_compile": _result("sim_compile"),
            "sim_run": _result("sim_run"),
        },
        None,
    ) == "L2"
    assert _raw_tool_pass_level(
        {
            "lint": _result("lint"),
            "sim_compile": _result("sim_compile"),
            "sim_run": _result("sim_run"),
            "synth": _result("synth"),
        },
        None,
    ) == "L3"
    assert _raw_tool_pass_level({}, {"h0": {"status": "fail"}}) == "H0_FAIL"


def test_episode_measurement_records_a_and_b() -> None:
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

    result = build_episode_measurement(
        attempts=attempts,
        patches=[_patch("d001", ["rtl/top.v"])],
        l4_open={"status": "not_run", "skip_reason": "not_selected_by_policy"},
    )

    assert result["initial"]["measurement_point"] == "a_first_attempt_no_tools"
    assert result["initial"]["attempt_id"] == 0
    assert result["initial"]["pass_level"] == "L1"
    assert result["final"]["measurement_point"] == "b_tool_in_loop_repair"
    assert result["final"]["attempt_id"] == 1
    assert result["final"]["pass_level"] == "L3"
    assert result["repair_attempts_used"] == 1
    assert result["repair_calls_attempted"] == 1
    assert result["repair_transitions"] == 1
    assert result["repair_accounting"]["status"] == "complete"
    assert result["repair_accounting"]["by_scope"]["project"] == {
        "calls_attempted": 1,
        "transitions": 1,
        "call_status_counts": {"succeeded": 1},
    }
    assert result["repair_success"] is True
    assert result["regressions"] == []
    assert result["l4_open"]["status"] == "not_run"


def test_episode_measurement_keeps_unrepaired_failure_scoreable() -> None:
    result = build_episode_measurement(
        attempts=[
            {
                "attempt_id": 0,
                "pass_level": "L0",
                "failure_type": "contract_mismatch",
                "automatic_pass_credit": True,
                "repair_eligible": False,
                "repair_skip_reason": "no_repairer",
            }
        ],
        patches=[],
    )

    assert result["initial"] == result["final"]
    assert result["repair_success"] is False
    assert result["repair_eligible"] is False
    assert result["repair_skip_reason"] == "no_repairer"
    assert result["infrastructure_status"] == "scoreable"


def test_episode_measurement_does_not_infer_repair_from_attempt_ids() -> None:
    result = build_episode_measurement(
        attempts=[
            {
                "attempt_id": 0,
                "pass_level": "L1",
                "failure_type": "simulation_mismatch",
                "repair_eligible": True,
            },
            {"attempt_id": 3, "pass_level": "L3", "failure_type": "none"},
        ],
        patches=[_patch("d001", ["rtl/top.v"])],
    )

    assert result["repair_attempts_used"] == 0
    assert result["repair_calls_attempted"] == 0
    assert result["repair_transitions"] == 0
    assert result["repair_success"] is False
    assert result["repair_accounting"]["status"] == "incomplete"
    assert "attempt_0:missing_repair_event_fields" in result["repair_accounting"]["issues"]


def test_episode_measurement_counts_failed_repair_call_but_not_transition() -> None:
    result = build_episode_measurement(
        attempts=[
            {
                "attempt_id": 0,
                "pass_level": "L1",
                "failure_type": "repair_failed",
                "repair_scope": "project",
                "repair_attempted": True,
                "repair_call_status": "failed",
            }
        ],
        patches=[],
    )

    assert result["repair_attempts_used"] == 0
    assert result["repair_calls_attempted"] == 1
    assert result["repair_transitions"] == 0
    assert result["repair_success"] is False
    assert result["repair_accounting"]["status"] == "complete"
    assert result["repair_accounting"]["by_scope"]["project"] == {
        "calls_attempted": 1,
        "transitions": 0,
        "call_status_counts": {"failed": 1},
    }


def test_episode_measurement_counts_failed_h_candidate_as_attempted_transition() -> None:
    result = build_episode_measurement(
        attempts=[
            {
                "attempt_id": 0,
                "pass_level": "H2_FAIL",
                "failure_type": "system_his_validation",
                "repair_scope": "system_his",
                "repair_attempted": True,
                "repair_call_status": "candidate_failed_validation",
            },
            {"attempt_id": 1, "pass_level": "H2_FAIL", "failure_type": "system_his_validation"},
        ],
        patches=[_patch("d001", ["system_his.json"])],
    )

    assert result["repair_attempts_used"] == 1
    assert result["repair_calls_attempted"] == 1
    assert result["repair_transitions"] == 1
    assert result["repair_success"] is False
    assert result["repair_accounting"]["by_scope"]["system_his"] == {
        "calls_attempted": 1,
        "transitions": 1,
        "call_status_counts": {"candidate_failed_validation": 1},
    }


def test_episode_measurement_requires_valid_patch_and_rerun() -> None:
    attempts = [
        {
            "attempt_id": 0,
            "pass_level": "L1",
            "failure_type": "simulation_mismatch",
            "repair_scope": "project",
            "repair_attempted": True,
            "repair_call_status": "succeeded",
        }
    ]
    result = build_episode_measurement(
        attempts=attempts,
        patches=[_patch("d001", ["rtl/top.v"], status="invalid_edit_surface")],
    )

    assert result["repair_calls_attempted"] == 1
    assert result["repair_transitions"] == 0
    assert result["repair_attempts_used"] == 0
    assert result["repair_accounting"]["status"] == "complete"

    missing_rerun = build_episode_measurement(
        attempts=attempts,
        patches=[_patch("d001", ["rtl/top.v"])],
    )
    assert missing_rerun["repair_transitions"] == 0
    assert missing_rerun["repair_accounting"]["status"] == "incomplete"
    assert "attempt_0:missing_rerun" in missing_rerun["repair_accounting"]["issues"]


def test_episode_measurement_excludes_infrastructure_outcome_from_model_denominator() -> None:
    result = build_episode_measurement(
        attempts=[
            {
                "attempt_id": 0,
                "pass_level": "L0",
                "failure_type": "oracle_bundle_error",
                "automatic_pass_credit": False,
                "infrastructure_reason": "independent_oracle_infrastructure_error",
            }
        ],
        patches=[],
    )

    assert result["infrastructure_status"] == "independent_oracle_infrastructure_error"
    assert result["scoreable"] is False


def test_collect_paired_results_groups_four_sources_and_reports_a_b(tmp_path: Path) -> None:
    paired_id = "fir_filter:0123456789abcdef"
    requirement_hash = "a" * 64
    sample_ids = []
    for index, source in enumerate(("claude", "gpt", "qwen", "deepseek")):
        sample_id = f"sample-{source}"
        sample_ids.append(sample_id)
        _write_sample(
            tmp_path,
            sample_id=sample_id,
            source=source,
            family_id="fir_filter",
            paired_id=paired_id,
            requirement_hash=requirement_hash,
            initial_level="L1" if index == 0 else "L3",
            final_level="L3",
            repair_success=index == 0,
        )

    result = collect_paired_results(tmp_path, sample_ids)

    assert result["schema_version"] == "sr2fpga-phase-d-paired-v1"
    assert result["episode_count"] == 4
    assert result["scoreable_episode_count"] == 4
    assert result["pair_count"] == 1
    assert result["complete_pairs"] == 1
    assert result["pairs"][0]["requirement_sha256"] == requirement_hash
    assert set(result["pairs"][0]["source_outcomes"]) == {"claude", "gpt", "qwen", "deepseek"}
    assert result["by_source"]["claude"]["initial"]["l3_pass"] == 0
    assert result["by_source"]["claude"]["final"]["l3_pass"] == 1
    assert result["by_family"]["fir_filter"]["repair_success"] == 1
    assert result["by_family"]["fir_filter"]["repair_calls_attempted"] == 1
    assert result["by_family"]["fir_filter"]["repair_transitions"] == 1
    assert result["by_family"]["fir_filter"]["repair_accounting"]["by_scope"]["project"][
        "transitions"
    ] == 1
    assert result["initial_vs_final"]["l3_pass_delta"] == 1


def test_collect_paired_results_rejects_duplicate_source(tmp_path: Path) -> None:
    for sample_id in ("sample-a", "sample-b"):
        _write_sample(
            tmp_path,
            sample_id=sample_id,
            source="claude",
            family_id="fir_filter",
            paired_id="fir_filter:pair",
            requirement_hash="a" * 64,
        )

    with pytest.raises(ValueError, match="duplicate source"):
        collect_paired_results(tmp_path, ["sample-a", "sample-b"])


def test_collect_paired_results_aggregates_repair_scopes_separately(tmp_path: Path) -> None:
    for source, scope in (("claude", "project"), ("gpt", "system_his")):
        _write_sample(
            tmp_path,
            sample_id=f"sample-{source}",
            source=source,
            family_id="fir_filter",
            paired_id="fir_filter:pair",
            requirement_hash="a" * 64,
            initial_level="L1",
            final_level="L3",
            repair_success=True,
            repair_scope=scope,
        )

    result = collect_paired_results(tmp_path, ["sample-claude", "sample-gpt"])
    scope_totals = result["by_family"]["fir_filter"]["repair_accounting"]["by_scope"]

    assert scope_totals["project"]["calls_attempted"] == 1
    assert scope_totals["project"]["transitions"] == 1
    assert scope_totals["system_his"]["calls_attempted"] == 1
    assert scope_totals["system_his"]["transitions"] == 1


def test_collect_paired_results_rejects_mismatched_requirement_hash(tmp_path: Path) -> None:
    _write_sample(
        tmp_path,
        sample_id="sample-a",
        source="claude",
        family_id="fir_filter",
        paired_id="fir_filter:pair",
        requirement_hash="a" * 64,
    )
    _write_sample(
        tmp_path,
        sample_id="sample-b",
        source="gpt",
        family_id="fir_filter",
        paired_id="fir_filter:pair",
        requirement_hash="b" * 64,
    )

    with pytest.raises(ValueError, match="requirement hash mismatch"):
        collect_paired_results(tmp_path, ["sample-a", "sample-b"])


def _write_sample(
    root: Path,
    *,
    sample_id: str,
    source: str,
    family_id: str,
    paired_id: str,
    requirement_hash: str,
    initial_level: str = "L1",
    final_level: str = "L1",
    repair_success: bool = False,
    repair_scope: str = "project",
) -> None:
    sample_dir = root / sample_id
    (sample_dir / "eval").mkdir(parents=True)
    (sample_dir / "metadata.json").write_text(
        json.dumps(
            {
                "source": source,
                "family_id": family_id,
                "paired_requirement_id": paired_id,
                "requirement_sha256": requirement_hash,
                "freeze_fingerprint": "f" * 64,
            }
        ),
        encoding="utf-8",
    )
    (sample_dir / "eval" / "labels.json").write_text(
        json.dumps({"pass_level": final_level, "automatic_pass_credit": True}),
        encoding="utf-8",
    )
    (sample_dir / "eval" / "trajectory.json").write_text(
        json.dumps(
            {
                "sample_id": sample_id,
                "measurement": {
                    "initial": {
                        "attempt_id": 0,
                        "pass_level": initial_level,
                        "failure_type": "simulation_mismatch" if initial_level != "L3" else "none",
                        "automatic_pass_credit": True,
                    },
                    "final": {
                        "attempt_id": 1 if repair_success else 0,
                        "pass_level": final_level,
                        "failure_type": "none" if final_level == "L3" else "simulation_mismatch",
                        "automatic_pass_credit": True,
                    },
                    "repair_attempts_used": 1 if repair_success else 0,
                    "repair_calls_attempted": 1 if repair_success else 0,
                    "repair_transitions": 1 if repair_success else 0,
                    "repair_accounting": {
                        "status": "complete",
                        "repair_calls_attempted": 1 if repair_success else 0,
                        "repair_transitions": 1 if repair_success else 0,
                        "by_scope": {
                            "system_his": {
                                "calls_attempted": (
                                    1 if repair_success and repair_scope == "system_his" else 0
                                ),
                                "transitions": (
                                    1 if repair_success and repair_scope == "system_his" else 0
                                ),
                                "call_status_counts": (
                                    {"succeeded": 1}
                                    if repair_success and repair_scope == "system_his"
                                    else {}
                                ),
                            },
                            "project": {
                                "calls_attempted": (
                                    1 if repair_success and repair_scope == "project" else 0
                                ),
                                "transitions": (
                                    1 if repair_success and repair_scope == "project" else 0
                                ),
                                "call_status_counts": (
                                    {"succeeded": 1}
                                    if repair_success and repair_scope == "project"
                                    else {}
                                ),
                            },
                        },
                        "issues": [],
                    },
                    "repair_success": repair_success,
                    "regressions": [],
                    "scoreable": True,
                    "infrastructure_status": "scoreable",
                    "l4_open": {"status": "not_run", "skip_reason": "not_selected_by_policy"},
                },
            }
        ),
        encoding="utf-8",
    )


def _patch(diagnosis_id: str, files_touched: list[str], *, status: str = "valid") -> dict:
    return {
        "diagnosis_id": diagnosis_id,
        "files_touched": files_touched,
        "allowed_edit_regions_respected": status == "valid",
        "touched_trusted_artifacts": False,
        "status": status,
        "regressions": [],
    }
