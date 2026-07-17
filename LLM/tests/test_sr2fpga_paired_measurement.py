import json
from pathlib import Path

import pytest

from LLM.src.sr2fpga_agent.agent import _raw_tool_pass_level
from LLM.src.sr2fpga_agent.models import ToolResult
from LLM.src.sr2fpga_agent.paired_measurement import (
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
        {"attempt_id": 0, "pass_level": "L1", "failure_type": "simulation_mismatch"},
        {"attempt_id": 1, "pass_level": "L3", "failure_type": "none"},
    ]

    result = build_episode_measurement(
        attempts=attempts,
        patches=[{"regressions": []}],
        l4_open={"status": "not_run", "skip_reason": "not_selected_by_policy"},
    )

    assert result["initial"]["measurement_point"] == "a_first_attempt_no_tools"
    assert result["initial"]["attempt_id"] == 0
    assert result["initial"]["pass_level"] == "L1"
    assert result["final"]["measurement_point"] == "b_tool_in_loop_repair"
    assert result["final"]["attempt_id"] == 1
    assert result["final"]["pass_level"] == "L3"
    assert result["repair_attempts_used"] == 1
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
