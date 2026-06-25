import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.baseline_report import (
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
