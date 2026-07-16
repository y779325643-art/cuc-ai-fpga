import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from LLM.src.sr2fpga_agent.agent import DataGenerationAgent, _labels
from LLM.src.sr2fpga_agent.baseline_report import baseline_rows, render_markdown
from LLM.src.sr2fpga_agent.failure_injector import oracle_mutation_projects
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ToolResult
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.models import ProjectRequest
from LLM.src.sr2fpga_agent.runner import (
    RunnerConfig,
    TaskConfig,
    initial_run_state,
    _summary as run_batch_summary_for_test,
)
from LLM.src.sr2fpga_agent.task_catalog import task_family_spec_for_family_id
from LLM.src.sr2fpga_agent.testbench_checker import (
    build_oracle_strength,
    oracle_strength_ready,
    oracle_strength_threshold,
)


class OracleStrengthTest(unittest.TestCase):
    def test_builds_oracle_strength_from_clean_reference_and_mutations(self) -> None:
        strength = build_oracle_strength(
            reference_pass=True,
            task_type="sync_fifo",
            mutation_results={
                "wrong_output": "failed",
                "missing_stall": "passed",
                "compile_only": None,
            },
        )

        self.assertEqual(
            strength,
            {
                "reference_pass": True,
                "mutation_cases": 2,
                "killed": 1,
                "mutation_score": 0.5,
                "surviving_mutations": ["missing_stall"],
                "non_scoreable_mutations": ["compile_only"],
                "task_family": "sync_fifo",
                "threshold": 0.85,
                "line_a_ready": False,
            },
        )

    def test_uses_catalog_thresholds_for_line_a_oracle_readiness(self) -> None:
        self.assertEqual(oracle_strength_threshold("fifo"), 0.85)
        self.assertEqual(oracle_strength_threshold("sync_fifo"), 0.85)
        self.assertEqual(oracle_strength_threshold("streaming_valid_ready"), 0.85)
        self.assertEqual(oracle_strength_threshold("fir_filter"), 0.85)
        self.assertEqual(oracle_strength_threshold("uart_tx"), 0.85)
        self.assertTrue(oracle_strength_ready("fir_filter", 0.85))
        self.assertFalse(oracle_strength_ready("fir_filter", 0.84))

    def test_mac_array_uses_the_complex_family_threshold_and_readiness(self) -> None:
        strength = build_oracle_strength(
            reference_pass=True,
            task_type="mac_array",
            mutation_results={**{f"killed_{index}": "failed" for index in range(9)}, "survives": "passed"},
        )

        self.assertEqual(strength["threshold"], 0.85)
        self.assertTrue(strength["line_a_ready"])

    def test_non_scoreable_catalog_mutation_blocks_line_a_readiness(self) -> None:
        strength = build_oracle_strength(
            reference_pass=True,
            task_type="fir_filter",
            mutation_results={"truncate_accumulator": "failed", "missing_stall": None},
        )

        self.assertEqual(strength["mutation_score"], 1.0)
        self.assertEqual(strength["non_scoreable_mutations"], ["missing_stall"])
        self.assertFalse(strength["line_a_ready"])

    def test_mac_array_uses_matrix_vector_mac_dut_only_mutation(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="matrix_vector_mac", width=8, project_name="matrix_vector_mac"),
            platform,
        )

        mutations = oracle_mutation_projects(project, "mac_array")

        self.assertTrue(mutations)
        self.assertEqual(tuple(mutations), task_family_spec_for_family_id("matrix_vector_mac").mutation_suite)
        mutation = mutations["wrong_lane_reduction"]
        self.assertIsNotNone(mutation)
        assert mutation is not None
        self.assertNotEqual(mutation.files["rtl/dot_product_engine.v"], project.files["rtl/dot_product_engine.v"])
        self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])

    def test_fir_oracle_mutations_implement_every_catalog_suite_entry(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="fir_filter", width=8, project_name="fir_filter"),
            platform,
        )

        mutations = oracle_mutation_projects(project, "fir_filter")

        self.assertEqual(tuple(mutations), task_family_spec_for_family_id("fir_filter").mutation_suite)
        self.assertNotIn(None, mutations.values())

    def test_not_ready_oracle_gates_official_l3_credit_but_preserves_tool_checks(self) -> None:
        labels = _labels(
            {
                "lint": _tool_result("lint", "passed"),
                "sim_compile": _tool_result("sim_compile", "passed"),
                "sim_run": _tool_result("sim_run", "passed"),
                "synth": _tool_result("synth", "passed"),
            },
            {"status": "not_run", "skip_reason": "disabled_by_config", "tool": None},
            final_attempt_id=0,
            failure_count=0,
            oracle_strength={"line_a_ready": False},
            enforce_oracle_readiness=True,
        )

        self.assertEqual(labels["pass_level"], "ORACLE_NOT_READY")
        self.assertEqual(labels["highest_official_level"], "ORACLE_NOT_READY")
        self.assertEqual(labels["raw_tool_pass_level"], "L3")
        self.assertFalse(labels["oracle_strength_line_a_ready"])
        self.assertTrue(labels["checks"]["l3_synth_pass"])

    def test_not_ready_oracle_does_not_gate_default_line_b_credit(self) -> None:
        labels = _labels(
            {
                "lint": _tool_result("lint", "passed"),
                "sim_compile": _tool_result("sim_compile", "passed"),
                "sim_run": _tool_result("sim_run", "passed"),
                "synth": _tool_result("synth", "passed"),
            },
            {"status": "not_run", "skip_reason": "disabled_by_config", "tool": None},
            final_attempt_id=0,
            failure_count=0,
            oracle_strength={"line_a_ready": False},
        )

        self.assertEqual(labels["pass_level"], "L3")
        self.assertEqual(labels["highest_official_level"], "L3")
        self.assertEqual(labels["raw_tool_pass_level"], "L3")
        self.assertFalse(labels["oracle_strength_line_a_ready"])

    def test_labels_without_oracle_strength_remain_unchanged(self) -> None:
        labels = _labels(
            {
                "lint": _tool_result("lint", "passed"),
                "sim_compile": _tool_result("sim_compile", "passed"),
                "sim_run": _tool_result("sim_run", "passed"),
                "synth": _tool_result("synth", "passed"),
            },
            {"status": "not_run", "skip_reason": "disabled_by_config", "tool": None},
            final_attempt_id=0,
            failure_count=0,
        )

        self.assertEqual(labels["pass_level"], "L3")
        self.assertEqual(labels["highest_official_level"], "L3")
        self.assertNotIn("raw_tool_pass_level", labels)
        self.assertNotIn("oracle_strength_line_a_ready", labels)

    def test_line_a_readiness_passes_and_fails_at_family_threshold(self) -> None:
        fifo_ready = build_oracle_strength(
            reference_pass=True,
            task_type="sync_fifo",
            mutation_results={**{f"killed_{index}": "failed" for index in range(6)}, "stall": "passed"},
        )
        stream_not_ready = build_oracle_strength(
            reference_pass=True,
            task_type="streaming_valid_ready",
            mutation_results={"wrong_data": "failed", "missing_stall": "failed", "wrong_valid": "failed", "survives": "passed"},
        )

        self.assertTrue(fifo_ready["line_a_ready"])
        self.assertEqual(fifo_ready["threshold"], 0.85)
        self.assertFalse(stream_not_ready["line_a_ready"])
        self.assertEqual(stream_not_ready["threshold"], 0.85)

    def test_agent_excludes_mutants_that_do_not_reach_sim_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = DataGenerationAgent(dataset_root=Path(tmp))
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            reference = GeneratedProject(project_name="fifo", files={"rtl/top.v": "reference"})
            rejected = GeneratedProject(project_name="fifo", files={"rtl/top.v": "rejected"})
            surviving = GeneratedProject(project_name="fifo", files={"rtl/top.v": "surviving"})
            compile_only = GeneratedProject(project_name="fifo", files={"rtl/top.v": "compile_only"})

            def run_pipeline(project, project_dir, pipeline_platform):
                marker = project.files["rtl/top.v"]
                if marker == "rejected":
                    return {
                        "sim_run": ToolResult(
                            stage="sim_run",
                            command=["vvp"],
                            status="failed",
                            exit_code=1,
                            stdout="TEST_FAIL signal=out_data cycle=17 expected=42 actual=41\n",
                            stderr="",
                            duration_seconds=0.01,
                        )
                    }
                if marker == "surviving":
                    return {"sim_run": _tool_result("sim_run", "passed")}
                return {"sim_compile": _tool_result("sim_compile", "failed")}

            agent._run_pipeline = run_pipeline
            with patch(
                "LLM.src.sr2fpga_agent.agent.oracle_mutation_projects",
                return_value={"rejected": rejected, "surviving": surviving, "compile_only": compile_only},
            ):
                strength = agent._oracle_strength(
                    reference,
                    Path(tmp) / "sample",
                    platform,
                    "sync_fifo",
                    {"sim_run": _tool_result("sim_run", "passed")},
                )
            rejected_dir = Path(tmp) / "sample/oracle_mutations/rejected"
            rejected_evidence_files = (
                (rejected_dir / "eval/sim_run.json").is_file(),
                (rejected_dir / "eval/sim_run.log").is_file(),
                (rejected_dir / "diagnosis.json").is_file(),
            )

        self.assertEqual(strength["mutation_cases"], 2)
        self.assertEqual(strength["killed"], 1)
        self.assertEqual(strength["surviving_mutations"], ["surviving"])
        self.assertEqual(strength["non_scoreable_mutations"], ["compile_only"])
        rejected_detail = strength["mutation_details"]["rejected"]
        self.assertEqual(rejected_detail["outcome"], "killed")
        self.assertEqual(rejected_detail["first_failure_stage"], "sim_run")
        self.assertEqual(rejected_detail["failure_type"], "functional_mismatch")
        self.assertEqual(
            rejected_detail["mismatch_detail"],
            [{"signal": "out_data", "cycle": 17, "expected": "42", "actual": "41"}],
        )
        self.assertEqual(rejected_evidence_files, (True, True, True))
        self.assertEqual(strength["mutation_details"]["surviving"]["outcome"], "survived")
        self.assertEqual(strength["mutation_details"]["compile_only"]["outcome"], "non_scoreable")

    def test_summary_aggregates_trajectory_mutation_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_dir = root / "datasets" / "sample_oracle" / "eval"
            sample_dir.mkdir(parents=True)
            (sample_dir / "labels.json").write_text(
                json.dumps({"pass_level": "L3", "checks": {"l0_complete": True}}),
                encoding="utf-8",
            )
            (sample_dir / "trajectory.json").write_text(
                json.dumps(
                    {
                        "oracle_strength": {
                            "reference_pass": True,
                            "mutation_cases": 12,
                            "killed": 11,
                            "mutation_score": 0.92,
                            "surviving_mutations": ["missing_stall"],
                            "non_scoreable_mutations": ["compile_only"],
                            "task_family": "sync_fifo",
                            "threshold": 0.75,
                            "line_a_ready": True,
                        }
                    }
                ),
                encoding="utf-8",
            )
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="fifo", widths=[8], count=1)],
            )
            state = initial_run_state("run_oracle")
            state = state.__class__(
                run_id=state.run_id,
                next_index=1,
                completed_samples=["sample_oracle"],
                buckets={"success_l3": ["sample_oracle"], "repair_trajectory": [], "rejected": []},
                failure_types={},
                exports_refreshed=False,
            )

            summary = run_batch_summary_for_test(config, state)

        self.assertEqual(
            summary["oracle_strength"],
            {
                "samples": 1,
                "reference_passed": 1,
                "mutation_cases": 12,
                "killed": 11,
                "mutation_score": 0.92,
                "surviving_mutations": {"missing_stall": 1},
                "non_scoreable_mutations": {"compile_only": 1},
                "line_a_ready": 1,
                "line_a_not_ready": 0,
            },
        )

    def test_report_renders_oracle_strength_information(self) -> None:
        summary = {
            "calibration_matrix": {},
            "oracle_strength": {
                "samples": 1,
                "reference_passed": 1,
                "mutation_cases": 12,
                "killed": 11,
                "mutation_score": 0.92,
                "surviving_mutations": {"missing_stall": 1},
                "non_scoreable_mutations": {"compile_only": 1},
                "line_a_ready": 1,
                "line_a_not_ready": 0,
            },
        }

        markdown = render_markdown("oracle-run", baseline_rows(summary), summary=summary)

        self.assertIn("## Testbench Oracle Strength", markdown)
        self.assertIn("| 1 | 1 | 12 | 11 | 92.0% | 1 | 0 |", markdown)
        self.assertIn("| missing_stall | 1 |", markdown)
        self.assertIn("| compile_only | 1 |", markdown)


if __name__ == "__main__":
    unittest.main()


def _tool_result(stage: str, status: str) -> ToolResult:
    return ToolResult(
        stage=stage,
        command=[stage],
        status=status,
        exit_code=0 if status == "passed" else 1,
        stdout="",
        stderr="",
        duration_seconds=0.0,
    )
