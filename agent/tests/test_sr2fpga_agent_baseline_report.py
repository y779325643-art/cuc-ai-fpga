import json
import tempfile
import unittest
from pathlib import Path

from sr2fpga_agent.baseline_report import (
    baseline_rows,
    detect_pass_rate_knee,
    main,
    render_markdown,
)


class BaselineReportTest(unittest.TestCase):
    def test_baseline_rows_extract_tier_and_topology_calibration(self) -> None:
        summary = _summary_fixture()

        rows = baseline_rows(summary)

        self.assertEqual(
            rows,
            [
                {
                    "group": "failure_family",
                    "value": "artifact_contract_failure",
                    "total": 1,
                    "pass_levels": {"L0": 1},
                    "l3_pass_rate": 0.0,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 1.0,
                },
                {
                    "group": "failure_origin",
                    "value": "natural_llm",
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
                {
                    "group": "difficulty_tier",
                    "value": "T1",
                    "total": 2,
                    "pass_levels": {"L3": 2},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
                {
                    "group": "difficulty_tier",
                    "value": "T4",
                    "total": 2,
                    "pass_levels": {"L0": 1, "L3": 1},
                    "l3_pass_rate": 0.5,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.5,
                },
                {
                    "group": "requirement_style",
                    "value": "natural_component",
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
                {
                    "group": "contract_skeleton_mode",
                    "value": "behavior_files",
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
                {
                    "group": "topology_id",
                    "value": "t1_event_counter",
                    "total": 2,
                    "pass_levels": {"L3": 2},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
                {
                    "group": "topology_id",
                    "value": "t4_dual_stream_join",
                    "total": 2,
                    "pass_levels": {"L0": 1, "L3": 1},
                    "l3_pass_rate": 0.5,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.5,
                },
                {
                    "group": "measurement_point",
                    "value": "a_first_attempt_no_tools",
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
            ],
        )

    def test_render_markdown_formats_rates_and_pass_levels_for_experiment_notes(self) -> None:
        markdown = render_markdown(
            "deepseek-baseline-a",
            baseline_rows(_summary_fixture()),
        )

        self.assertIn("# SR2FPGA Baseline Report: deepseek-baseline-a", markdown)
        self.assertIn("Pass-rate knee: T4 (L3 pass rate 50.0% < 80.0%).", markdown)
        self.assertIn("| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |", markdown)
        self.assertIn("| requirement_style | natural_component | 4 | L0:1, L3:3 | 75.0% | 1 | 25.0% |", markdown)
        self.assertIn("| contract_skeleton_mode | behavior_files | 4 | L0:1, L3:3 | 75.0% | 1 | 25.0% |", markdown)
        self.assertIn("| failure_family | artifact_contract_failure | 1 | L0:1 | 0.0% | 1 | 100.0% |", markdown)
        self.assertIn("| failure_origin | natural_llm | 4 | L0:1, L3:3 | 75.0% | 1 | 25.0% |", markdown)
        self.assertIn("| difficulty_tier | T4 | 2 | L0:1, L3:1 | 50.0% | 1 | 50.0% |", markdown)
        self.assertTrue(markdown.endswith("\n"))

    def test_render_markdown_includes_latent_testbench_issue_summary(self) -> None:
        summary = _summary_fixture()
        summary["latent_testbench_issue_breakdown"] = {"testbench_observation_race": 5}

        markdown = render_markdown(
            "deepseek-baseline-a",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## Latent Testbench Issues", markdown)
        self.assertIn("| issue_type | count |", markdown)
        self.assertIn("| testbench_observation_race | 5 |", markdown)

    def test_render_markdown_surfaces_line_a_readiness_counts(self) -> None:
        summary = _summary_fixture()
        summary["oracle_strength"] = {
            "samples": 2,
            "reference_passed": 2,
            "mutation_cases": 4,
            "killed": 3,
            "mutation_score": 0.75,
            "surviving_mutations": {"survives": 1},
            "non_scoreable_mutations": {"compile_only": 1},
            "line_a_ready": 1,
            "line_a_not_ready": 1,
        }

        markdown = render_markdown("oracle-readiness", baseline_rows(summary), summary=summary)

        self.assertIn("| samples | reference passed | mutation cases | killed | mutation score | Line A ready | Line A not ready |", markdown)
        self.assertIn("| 2 | 2 | 4 | 3 | 75.0% | 1 | 1 |", markdown)
        self.assertIn("| compile_only | 1 |", markdown)

    def test_render_markdown_includes_patch_repair_metrics(self) -> None:
        summary = _summary_fixture()
        summary["repair_metrics"] = {
            "total_patches": 5,
            "valid_patches": 4,
            "invalid_edit_surface": 1,
            "fixed_target": 3,
            "automatic_pass_credit": 2,
            "regressing_patches": 1,
            "regression_rate": 0.25,
        }

        markdown = render_markdown("patch-metrics", baseline_rows(summary), summary=summary)

        self.assertIn("## Patch-as-PR Repair", markdown)
        self.assertIn(
            "| total patches | valid patches | invalid edit surface | fixed target | automatic pass credit | regressing patches | regression rate |",
            markdown,
        )
        self.assertIn("| 5 | 4 | 1 | 3 | 2 | 1 | 25.0% |", markdown)

    def test_render_markdown_includes_phase_d_paired_initial_final_results(self) -> None:
        summary = _summary_fixture()
        summary["paired_results"] = {
            "episode_count": 4,
            "scoreable_episode_count": 3,
            "pair_count": 1,
            "complete_pairs": 1,
            "infrastructure_outcomes": {"provider_unavailable": 1},
            "initial_vs_final": {
                "scoreable_denominator": 3,
                "initial": {"l0_pass": 3, "l1_pass": 2, "l2_pass": 1, "l3_pass": 1},
                "final": {"l0_pass": 3, "l1_pass": 3, "l2_pass": 2, "l3_pass": 2},
                "repair_success": 1,
                "regressions": 0,
            },
            "by_source": {
                "claude": {
                    "episodes": 1,
                    "initial": {"l0_pass": 1, "l1_pass": 0, "l2_pass": 0, "l3_pass": 0},
                    "final": {"l0_pass": 1, "l1_pass": 1, "l2_pass": 1, "l3_pass": 1},
                    "repair_success": 1,
                    "regressions": 0,
                    "l4_open": {"not_run": 1},
                }
            },
            "by_family": {
                "fir_filter": {
                    "episodes": 1,
                    "initial": {"l0_pass": 1, "l1_pass": 0, "l2_pass": 0, "l3_pass": 0},
                    "final": {"l0_pass": 1, "l1_pass": 1, "l2_pass": 1, "l3_pass": 1},
                    "repair_success": 1,
                    "regressions": 0,
                    "l4_open": {"pass": 1},
                }
            },
        }

        markdown = render_markdown("phase-d", baseline_rows(summary), summary=summary)

        self.assertIn("## Phase D Paired Pilot", markdown)
        self.assertIn("Episodes: 4 total, 3 scoreable; pairs: 1/1 complete.", markdown)
        self.assertIn("### Initial (a) vs Final (b)", markdown)
        self.assertIn("| L3 | 1 | 2 | +1 |", markdown)
        self.assertIn("| claude | 1 | 0 | 1 | 1 | 0 | not_run:1 |", markdown)
        self.assertIn("| fir_filter | 1 | 0 | 1 | 1 | 0 | pass:1 |", markdown)
        self.assertIn("| provider_unavailable | 1 |", markdown)

    def test_render_markdown_includes_l4_open_counts_and_skip_histogram(self) -> None:
        summary = _summary_fixture()
        summary["l4_open"] = {"pass": 2, "fail": 1, "not_run": 3}
        summary["l4_open_skip_reasons"] = {"disabled_by_config": 2, "l3_failed": 1}

        markdown = render_markdown(
            "deepseek-baseline-a",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## L4-open", markdown)
        self.assertIn("| pass | fail | not_run |", markdown)
        self.assertIn("| 2 | 1 | 3 |", markdown)
        self.assertIn("| skip_reason | count |", markdown)
        self.assertIn("| disabled_by_config | 2 |", markdown)
        self.assertIn("| l3_failed | 1 |", markdown)

    def test_render_markdown_includes_l4_commercial_counts_and_skip_histogram(self) -> None:
        summary = _summary_fixture()
        summary["l4_commercial"] = {"pass": 2, "fail": 1, "not_run": 4}
        summary["l4_commercial_skip_reasons"] = {
            "disabled_by_config": 3,
            "l3_failed": 1,
        }

        markdown = render_markdown(
            "commercial-reference",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## L4-commercial", markdown)
        self.assertIn("| 2 | 1 | 4 |", markdown)
        self.assertIn("| disabled_by_config | 3 |", markdown)
        self.assertIn("| l3_failed | 1 |", markdown)

    def test_render_markdown_marks_req2file_as_derived_without_project_pass_credit(self) -> None:
        summary = _summary_fixture()
        summary["derived_training_views"] = {
            "req2file": {
                "available": True,
                "rows": 8,
                "file_level_passed": 8,
                "official_eval_unit": False,
                "standalone_pass_credit": False,
            }
        }

        markdown = render_markdown(
            "deepseek-baseline-a",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## Derived Training Views", markdown)
        self.assertIn("| view | available | official eval unit | standalone pass credit | rows | file-level passed |", markdown)
        self.assertIn("| req2file | yes | no | no | 8 | 8 |", markdown)
        self.assertNotIn("| req2file | yes | yes |", markdown)

    def test_render_markdown_includes_l0_l4_survival_curve(self) -> None:
        summary = _summary_fixture()
        summary["levels"] = {
            "l0": {"pass": 4, "fail": 1},
            "l1": {"pass": 3, "fail": 2},
            "l2": {"pass": 2, "fail": 3},
            "l3": {"pass": 2, "fail": 3},
            "l4_open": {"pass": 1, "fail": 1, "not_run": 3},
        }

        markdown = render_markdown(
            "deepseek-baseline-a",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## L0-L4 Survival", markdown)
        self.assertIn("| level | pass | fail | not_run |", markdown)
        self.assertIn("| l3 | 2 | 3 | 0 |", markdown)
        self.assertIn("| l4_open | 1 | 1 | 3 |", markdown)

    def test_render_markdown_includes_h_stage_summary(self) -> None:
        summary = _summary_fixture()
        summary["h_stage"] = {
            "h0": {"pass": 4, "fail": 0},
            "h1": {"pass": 3, "fail": 1},
            "h2": {"pass": 3, "fail": 1},
            "h3": {"pass": 2, "fail": 1, "not_applicable": 1},
        }

        markdown = render_markdown(
            "deepseek-baseline-a",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## H0-H3 Summary", markdown)
        self.assertIn("| stage | pass | fail | not_applicable |", markdown)
        self.assertIn("| h3 | 2 | 1 | 1 |", markdown)

    def test_render_markdown_includes_generated_his_credit_summary(self) -> None:
        summary = _summary_fixture()
        summary["generated_his_credit"] = {"credited": 3, "no_credit_oracle_fallback": 1}
        summary["generated_his_pass_level_breakdown"] = {"L3": 2, "H3_FAIL": 1}

        markdown = render_markdown(
            "deepseek-baseline-a",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## Generated-HIS Credit", markdown)
        self.assertIn("| credit_bucket | count |", markdown)
        self.assertIn("| credited | 3 |", markdown)
        self.assertIn("| no_credit_oracle_fallback | 1 |", markdown)
        self.assertIn("| generated_his_pass_level | count |", markdown)
        self.assertIn("| L3 | 2 |", markdown)

    def test_render_markdown_includes_contract_skeleton_ablation_summary(self) -> None:
        summary = _summary_fixture()
        summary["calibration_matrix"]["contract_skeleton_mode"]["legacy_full_project"] = {
            "total": 4,
            "pass_levels": {"L0_FAIL": 2, "L0": 1, "L3": 1},
            "l3_pass_rate": 0.25,
            "l0_contract_failures": 2,
            "cross_file_consistency_error_rate": 0.5,
        }

        markdown = render_markdown(
            "l0-by-construction-ablation",
            baseline_rows(summary),
            summary=summary,
        )

        self.assertIn("## Contract Skeleton Ablation", markdown)
        self.assertIn("| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |", markdown)
        self.assertIn("| legacy_full_project | 4 | L0:1, L0_FAIL:2, L3:1 | 25.0% | 2 | 50.0% |", markdown)
        self.assertIn("| behavior_files | 4 | L0:1, L3:3 | 75.0% | 1 | 25.0% |", markdown)
        self.assertIn("L0 contract failure delta (behavior_files - legacy_full_project): -1", markdown)
        self.assertIn("L3 pass-rate delta (behavior_files - legacy_full_project): +50.0 pp", markdown)

    def test_detect_pass_rate_knee_returns_first_tier_below_threshold(self) -> None:
        knee = detect_pass_rate_knee(baseline_rows(_summary_fixture()), threshold=0.8)

        self.assertEqual(knee["value"], "T4")
        self.assertEqual(knee["l3_pass_rate"], 0.5)

    def test_detect_pass_rate_knee_returns_empty_when_all_tiers_pass_threshold(self) -> None:
        rows = [
            {"group": "difficulty_tier", "value": "T1", "l3_pass_rate": 1.0},
            {"group": "difficulty_tier", "value": "T2", "l3_pass_rate": 0.9},
        ]

        self.assertEqual(detect_pass_rate_knee(rows, threshold=0.8), {})

    def test_main_writes_markdown_report_from_summary_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "summary.json"
            output_path = root / "baseline_report.md"
            summary_path.write_text(json.dumps(_summary_fixture()), encoding="utf-8")

            main(["--summary", str(summary_path), "--output", str(output_path)])

            text = output_path.read_text(encoding="utf-8")
            self.assertIn("deepseek-baseline-a", text)
            self.assertIn("t4_dual_stream_join", text)


def _summary_fixture() -> dict[str, object]:
    return {
        "run_id": "deepseek-baseline-a",
        "calibration_matrix": {
            "failure_origin": {
                "natural_llm": {
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
            },
            "failure_family": {
                "artifact_contract_failure": {
                    "total": 1,
                    "pass_levels": {"L0": 1},
                    "l3_pass_rate": 0.0,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 1.0,
                },
            },
            "difficulty_tier": {
                "T4": {
                    "total": 2,
                    "pass_levels": {"L0": 1, "L3": 1},
                    "l3_pass_rate": 0.5,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.5,
                },
                "T1": {
                    "total": 2,
                    "pass_levels": {"L3": 2},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            },
            "requirement_style": {
                "natural_component": {
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
            },
            "contract_skeleton_mode": {
                "behavior_files": {
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
            },
            "topology_id": {
                "t4_dual_stream_join": {
                    "total": 2,
                    "pass_levels": {"L0": 1, "L3": 1},
                    "l3_pass_rate": 0.5,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.5,
                },
                "t1_event_counter": {
                    "total": 2,
                    "pass_levels": {"L3": 2},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            },
            "measurement_point": {
                "a_first_attempt_no_tools": {
                    "total": 4,
                    "pass_levels": {"L0": 1, "L3": 3},
                    "l3_pass_rate": 0.75,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 0.25,
                },
            },
        },
    }


if __name__ == "__main__":
    unittest.main()
