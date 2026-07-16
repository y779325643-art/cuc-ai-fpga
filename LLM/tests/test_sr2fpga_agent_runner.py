import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from LLM.src.sr2fpga_agent.baseline_report import baseline_rows, render_markdown
from LLM.src.sr2fpga_agent.runner import (
    L4CommercialConfig,
    L4OpenConfig,
    PlannedSample,
    RunState,
    RunnerConfig,
    SourceConnection,
    TaskConfig,
    classify_sample_bucket,
    initial_run_state,
    load_runner_config,
    planned_samples,
    read_run_state,
    run_batch,
    runner_preflight,
    should_skip_sample,
    write_run_state,
    _failure_family,
    _l4_open_enabled_for_config,
    _l4_open_enabled_for_sample,
    _record_completed as _record_completed_for_test,
    _sample_system_his_schema_version,
    _source_auth_diagnostics,
    _summary as run_batch_summary_for_test,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class RunnerConfigTest(unittest.TestCase):
    def test_phase_c_independent_oracle_config_plans_nine_explicit_aliases(self) -> None:
        config = load_runner_config(
            REPO_ROOT
            / "configs"
            / "current"
            / "sr2fpga_phase_c_independent_oracle.example.yaml"
        )

        self.assertEqual(config.provider, "deterministic")
        self.assertTrue(
            all(sample.evaluation_line == "line_a" for sample in planned_samples(config))
        )
        self.assertTrue(config.run_independent_oracle)
        self.assertFalse(config.run_l4_open)
        self.assertFalse(config.run_l4_commercial)
        self.assertEqual(config.max_attempts, 1)
        self.assertEqual(len(config.tasks), 9)
        self.assertEqual(len(planned_samples(config)), 9)
        self.assertEqual(
            [sample.task_type for sample in planned_samples(config)],
            [
                "fir_filter",
                "matrix_vector_mac",
                "matched_filter",
                "peak_detector",
                "pulse_radar_signal",
                "sobel_threshold",
                "vision_defect_core",
                "t6_td_update_core",
                "t10_rl_accelerator_shell",
            ],
        )

    def test_load_runner_config_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": True,
                        "line_b_targets": {
                            "l3_success_ratio": 0.4,
                            "repair_trajectory_ratio": 0.6,
                            "max_samples": 3,
                        },
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4, 8],
                                "count": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertEqual(config.dataset_root, Path("datasets/sr2fpga_rtl_v1"))
            self.assertEqual(config.export_root, Path("datasets/sr2fpga_rtl_v1_exports"))
            self.assertEqual(config.run_root, Path("tmp/sr2fpga_runs"))
            self.assertEqual(config.provider, "deterministic")
            self.assertEqual(config.repair_provider, "none")
            self.assertEqual(config.model, "deepseek-v4-pro")
            self.assertEqual(config.max_attempts, 1)
            self.assertTrue(config.refresh_exports)
            self.assertEqual(config.env_file, Path(""))
            self.assertEqual(config.line_b_targets["l3_success_ratio"], 0.4)
            self.assertEqual(config.line_b_targets["repair_trajectory_ratio"], 0.6)
            self.assertEqual(config.line_b_targets["max_samples"], 3)
            self.assertEqual(config.tasks[0].source, "deterministic")
            self.assertEqual(config.tasks[0].task_type, "counter")
            self.assertEqual(config.tasks[0].widths, [4, 8])
            self.assertEqual(config.tasks[0].count, 2)
            self.assertEqual(config.tasks[0].failure_injectors, [])
            self.assertEqual(config.tasks[0].difficulty_tier, "")
            self.assertEqual(config.tasks[0].failure_origin, "")
            self.assertEqual(config.tasks[0].topology_ids, [])
            self.assertEqual(config.tasks[0].measurement_point, "")
            self.assertEqual(config.tasks[0].requirement_style, "contract")
            self.assertFalse(config.run_independent_oracle)

    def test_load_runner_config_parses_independent_oracle_switch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "run_independent_oracle": True,
                        "line_b_targets": {"max_samples": 1},
                        "tasks": [{"task_type": "counter", "widths": [8], "count": 1}],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertTrue(config.run_independent_oracle)

    def test_load_runner_config_parses_openxc7_l4_switch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": True,
                        "enable_openxc7_l4": True,
                        "line_b_targets": {"max_samples": 1},
                        "tasks": [{"task_type": "counter", "widths": [8], "count": 1}],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertTrue(config.enable_openxc7_l4)
            self.assertEqual(config.l4_open.run_policy, "after_l3_pass")
            self.assertTrue(_l4_open_enabled_for_config(config))

    def test_load_runner_config_parses_l4_open_policy_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": True,
                        "run_l4_open": True,
                        "l4_open": {
                            "tool": "openxc7_nextpnr",
                            "target_part": "XC7Z020CLG484-2",
                            "board_profile": "ac820_zynq",
                            "run_policy": "after_l3_pass",
                            "timeout_seconds": 600,
                        },
                        "line_b_targets": {"max_samples": 1},
                        "tasks": [{"task_type": "counter", "widths": [8], "count": 1}],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertTrue(config.enable_openxc7_l4)
            self.assertTrue(config.run_l4_open)
            self.assertEqual(config.l4_open.tool, "openxc7_nextpnr")
            self.assertEqual(config.l4_open.target_part, "XC7Z020CLG484-2")
            self.assertEqual(config.l4_open.board_profile, "ac820_zynq")
            self.assertEqual(config.l4_open.run_policy, "after_l3_pass")
            self.assertEqual(config.l4_open.timeout_seconds, 600)

    def test_load_runner_config_parses_l4_commercial_policy_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": True,
                        "run_l4_commercial": True,
                        "l4_commercial": {
                            "tool": "vivado",
                            "command": "vivado.bat",
                            "target_part": "XC7Z020CLG484-2",
                            "run_policy": "representative_subset",
                            "timeout_seconds": 1800,
                        },
                        "line_b_targets": {"max_samples": 1},
                        "tasks": [{"task_type": "fir_filter", "widths": [8], "count": 1}],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertTrue(config.run_l4_commercial)
            self.assertEqual(config.l4_commercial.tool, "vivado")
            self.assertEqual(config.l4_commercial.command, "vivado.bat")
            self.assertEqual(config.l4_commercial.target_part, "XC7Z020CLG484-2")
            self.assertEqual(config.l4_commercial.run_policy, "representative_subset")
            self.assertEqual(config.l4_commercial.timeout_seconds, 1800)

    def test_run_batch_passes_l4_open_config_to_agent(self) -> None:
        captured_kwargs: dict[str, object] = {}

        class FakeAgent:
            def __init__(self, dataset_root, *args, **kwargs):
                self.dataset_root = Path(dataset_root)
                captured_kwargs.update(kwargs)

            def run_one(self, sample_id, requirement, request, platform, metadata=None):
                eval_dir = self.dataset_root / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3",
                            "l4_open_status": "not_run",
                            "l4_open_skip_reason": "not_selected_by_policy",
                            "checks": {"l0_complete": True, "l3_synth_pass": True},
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (self.dataset_root / sample_id / "metadata.json").write_text(
                    json.dumps(metadata or {}) + "\n",
                    encoding="utf-8",
                )
                return {"sample_dir": str(self.dataset_root / sample_id), "pass_level": "L3"}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
                enable_openxc7_l4=True,
                run_l4_open=True,
                l4_open=L4OpenConfig(
                    tool="openxc7_nextpnr",
                    target_part="XC7Z020CLG484-2",
                    board_profile="ac820_zynq",
                    run_policy="after_l3_pass",
                    timeout_seconds=9,
                ),
            )

            with patch("LLM.src.sr2fpga_agent.runner.DataGenerationAgent", FakeAgent):
                run_batch(config, run_id="run_l4_config")

            self.assertTrue(captured_kwargs["enable_openxc7_l4"])
            self.assertEqual(captured_kwargs["openxc7_tool"], "openxc7_nextpnr")
            self.assertEqual(captured_kwargs["openxc7_part"], "XC7Z020CLG484-2")
            self.assertEqual(captured_kwargs["openxc7_board_profile"], "ac820_zynq")
            self.assertEqual(captured_kwargs["openxc7_timeout_seconds"], 9)

    def test_run_batch_passes_independent_oracle_config_to_agent(self) -> None:
        captured_kwargs: dict[str, object] = {}

        class FakeAgent:
            def __init__(self, dataset_root, *args, **kwargs):
                self.dataset_root = Path(dataset_root)
                captured_kwargs.update(kwargs)

            def run_one(self, sample_id, requirement, request, platform, metadata=None):
                eval_dir = self.dataset_root / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3",
                            "independent_oracle_status": "not_run",
                            "checks": {"l0_complete": True, "l3_synth_pass": True},
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (self.dataset_root / sample_id / "metadata.json").write_text(
                    json.dumps(metadata or {}) + "\n",
                    encoding="utf-8",
                )
                return {"sample_dir": str(self.dataset_root / sample_id), "pass_level": "L3"}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
                run_independent_oracle=True,
            )

            with patch("LLM.src.sr2fpga_agent.runner.DataGenerationAgent", FakeAgent):
                run_batch(config, run_id="run_independent_oracle_config")

            self.assertTrue(captured_kwargs["enable_independent_oracle"])

    def test_run_batch_passes_l4_commercial_config_to_agent(self) -> None:
        captured_kwargs: dict[str, object] = {}

        class FakeAgent:
            def __init__(self, dataset_root, *args, **kwargs):
                self.dataset_root = Path(dataset_root)
                captured_kwargs.update(kwargs)

            def run_one(self, sample_id, requirement, request, platform, metadata=None):
                eval_dir = self.dataset_root / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3",
                            "l4_open_status": "not_run",
                            "l4_open_skip_reason": "disabled_by_config",
                            "l4_commercial_status": "not_run",
                            "l4_commercial_skip_reason": "not_selected_by_policy",
                            "checks": {"l0_complete": True, "l3_synth_pass": True},
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (self.dataset_root / sample_id / "metadata.json").write_text(
                    json.dumps(metadata or {}) + "\n",
                    encoding="utf-8",
                )
                return {"sample_dir": str(self.dataset_root / sample_id), "pass_level": "L3"}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="fir_filter", widths=[8], count=1)],
                run_l4_commercial=True,
                l4_commercial=L4CommercialConfig(
                    tool="vivado",
                    command="vivado.bat",
                    target_part="XC7Z020CLG484-2",
                    run_policy="after_l3_pass",
                    timeout_seconds=90,
                ),
            )

            with patch("LLM.src.sr2fpga_agent.runner.DataGenerationAgent", FakeAgent):
                run_batch(config, run_id="run_l4_commercial_config")

            self.assertTrue(captured_kwargs["enable_vivado_l4"])
            self.assertEqual(captured_kwargs["vivado_tool"], "vivado")
            self.assertEqual(captured_kwargs["vivado_command"], "vivado.bat")
            self.assertEqual(captured_kwargs["vivado_part"], "XC7Z020CLG484-2")
            self.assertEqual(captured_kwargs["vivado_timeout_seconds"], 90)

    def test_run_batch_never_policy_disables_l4_open(self) -> None:
        captured_kwargs: dict[str, object] = {}

        class FakeAgent:
            def __init__(self, dataset_root, *args, **kwargs):
                self.dataset_root = Path(dataset_root)
                captured_kwargs.update(kwargs)

            def run_one(self, sample_id, requirement, request, platform, metadata=None):
                eval_dir = self.dataset_root / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3",
                            "l4_open_status": "not_run",
                            "l4_open_skip_reason": "disabled_by_config",
                            "checks": {"l0_complete": True, "l3_synth_pass": True},
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (self.dataset_root / sample_id / "metadata.json").write_text(
                    json.dumps(metadata or {}) + "\n",
                    encoding="utf-8",
                )
                return {"sample_dir": str(self.dataset_root / sample_id), "pass_level": "L3"}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
                enable_openxc7_l4=True,
                run_l4_open=True,
                l4_open=L4OpenConfig(run_policy="never"),
            )

            with patch("LLM.src.sr2fpga_agent.runner.DataGenerationAgent", FakeAgent):
                run_batch(config, run_id="run_l4_policy_never")

            self.assertFalse(captured_kwargs["enable_openxc7_l4"])

    def test_l4_open_policy_enablement_is_explicit(self) -> None:
        expected = {
            "never": False,
            "after_l3_pass": True,
            "representative_subset": False,
            "always": True,
        }

        for run_policy, enabled in expected.items():
            with self.subTest(run_policy=run_policy):
                config = RunnerConfig(
                    dataset_root=Path("datasets"),
                    export_root=Path("exports"),
                    run_root=Path("runs"),
                    provider="deterministic",
                    repair_provider="none",
                    max_attempts=1,
                    refresh_exports=False,
                    line_b_targets={"max_samples": 1},
                    tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
                    enable_openxc7_l4=True,
                    run_l4_open=True,
                    l4_open=L4OpenConfig(run_policy=run_policy),
                )

                self.assertEqual(_l4_open_enabled_for_config(config), enabled)

    def test_representative_subset_l4_policy_uses_catalog_targeting(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets"),
            export_root=Path("exports"),
            run_root=Path("runs"),
            provider="deterministic",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=False,
            line_b_targets={"max_samples": 2},
            tasks=[],
            enable_openxc7_l4=True,
            run_l4_open=True,
            l4_open=L4OpenConfig(run_policy="representative_subset"),
        )
        counter = PlannedSample("counter-1", "deterministic", "counter", 8, "counter", "counter")
        fir = PlannedSample("fir-1", "deterministic", "fir_filter", 8, "fir", "fir")
        flagship = PlannedSample(
            "rl-1",
            "deterministic",
            "composed_rl_accelerator_shell",
            8,
            "rl",
            "rl",
            topology_id="t10_rl_accelerator_shell",
        )

        self.assertFalse(_l4_open_enabled_for_sample(config, counter))
        self.assertTrue(_l4_open_enabled_for_sample(config, fir))
        self.assertTrue(_l4_open_enabled_for_sample(config, flagship))

    def test_load_runner_config_rejects_unknown_l4_open_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets",
                        "export_root": "exports",
                        "run_root": "runs",
                        "tasks": [{"task_type": "counter"}],
                        "l4_open": {"run_policy": "sometimes"},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SystemExit, "l4_open.run_policy"):
                load_runner_config(config_path)

    def test_load_runner_config_parses_task_failure_injectors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4],
                                "count": 1,
                                "difficulty_tier": "T0",
                                "failure_origin": "synthetic_injected",
                                "measurement_point": "b_tool_in_loop_repair",
                                "evaluation_line": "line_a",
                                "failure_injectors": ["rename_reset_port"],
                                "requirement_style": "natural_component",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertEqual(config.tasks[0].failure_injectors, ["rename_reset_port"])
            self.assertEqual(config.tasks[0].difficulty_tier, "T0")
            self.assertEqual(config.tasks[0].failure_origin, "synthetic_injected")
            self.assertEqual(config.tasks[0].measurement_point, "b_tool_in_loop_repair")
            self.assertEqual(config.tasks[0].evaluation_line, "line_a")
            self.assertEqual(config.tasks[0].requirement_style, "natural_component")
            sample = planned_samples(config)[0]
            self.assertEqual(sample.evaluation_line, "line_a")
            self.assertEqual(sample.metadata(config)["evaluation_line"], "line_a")

    def test_load_runner_config_rejects_unknown_evaluation_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets",
                        "export_root": "exports",
                        "run_root": "runs",
                        "tasks": [
                            {
                                "task_type": "counter",
                                "evaluation_line": "official",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SystemExit, "evaluation_line"):
                load_runner_config(config_path)

    def test_baseline_b_example_config_is_tool_loop_repair_measurement(self) -> None:
        config = load_runner_config(Path("configs/legacy/sr2fpga_baseline_b.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.repair_provider, "deepseek")
        self.assertGreater(config.max_attempts, 1)
        self.assertEqual(config.env_file, Path(".env"))
        self.assertEqual(config.sample_id_prefix, "baseline_b")
        self.assertEqual(len(samples), 4)
        self.assertEqual(samples[0].sample_id, "sample_baseline_b_t1_event_counter_8_000001")
        self.assertEqual({sample.metadata(config)["measurement_point"] for sample in samples}, {"b_tool_in_loop_repair"})
        self.assertEqual({sample.metadata(config)["failure_origin"] for sample in samples}, {"natural_llm"})
        self.assertEqual({sample.requirement_style for sample in samples}, {"natural_component"})
        self.assertEqual(
            [sample.topology_id for sample in samples],
            ["t1_event_counter", "t2_stream_accumulator", "t3_stream_fork", "t4_dual_stream_join"],
        )

    def test_line_a_oracle_evidence_config_uses_catalog_tiers_and_line_a_gate(self) -> None:
        config = load_runner_config(Path("configs/current/sr2fpga_line_a_oracle_evidence.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(len(samples), 6)
        self.assertEqual({sample.evaluation_line for sample in samples}, {"line_a"})
        self.assertEqual(
            {sample.task_type: sample.difficulty_tier for sample in samples},
            {
                "fifo": "T0",
                "uart_tx": "T0",
                "spi_master": "T1",
                "streaming_valid_ready": "T2",
                "fir_filter": "T3",
                "matrix_vector_mac": "T3",
            },
        )

    def test_line_a_l4_representative_config_targets_catalog_subset(self) -> None:
        config = load_runner_config(Path("configs/current/sr2fpga_line_a_l4_representative.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(len(samples), 2)
        self.assertEqual({sample.evaluation_line for sample in samples}, {"line_a"})
        self.assertEqual({sample.task_type for sample in samples}, {"fir_filter", "matrix_vector_mac"})
        self.assertEqual({sample.difficulty_tier for sample in samples}, {"T3"})
        self.assertEqual(config.l4_open.run_policy, "representative_subset")
        self.assertEqual(config.l4_open.target_part, "XC7Z020CLG484-2")
        self.assertEqual(config.l4_open.board_profile, "ac820_zynq")
        self.assertTrue(all(_l4_open_enabled_for_sample(config, sample) for sample in samples))

    def test_baseline_b_smoke_config_uses_tightened_prompt_namespace(self) -> None:
        config = load_runner_config(Path("configs/legacy/sr2fpga_baseline_b_smoke.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.repair_provider, "deepseek")
        self.assertEqual(config.max_attempts, 4)
        self.assertEqual(config.sample_id_prefix, "baseline_b_smoke")
        self.assertEqual([sample.topology_id for sample in samples], ["t1_event_counter", "t2_stream_accumulator"])
        self.assertEqual(
            [sample.sample_id for sample in samples],
            [
                "sample_baseline_b_smoke_t1_event_counter_8_000001",
                "sample_baseline_b_smoke_t2_stream_accumulator_8_000002",
            ],
        )
        self.assertEqual({sample.metadata(config)["measurement_point"] for sample in samples}, {"b_tool_in_loop_repair"})

    def test_baseline_b_tightened_config_runs_full_tier_set_in_new_namespace(self) -> None:
        config = load_runner_config(Path("configs/legacy/sr2fpga_baseline_b_tightened.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.repair_provider, "deepseek")
        self.assertEqual(config.max_attempts, 4)
        self.assertEqual(config.sample_id_prefix, "baseline_b_tightened")
        self.assertEqual([sample.topology_id for sample in samples], [
            "t1_event_counter",
            "t2_stream_accumulator",
            "t3_stream_fork",
            "t4_dual_stream_join",
        ])
        self.assertEqual(samples[0].sample_id, "sample_baseline_b_tightened_t1_event_counter_8_000001")
        self.assertEqual(samples[-1].sample_id, "sample_baseline_b_tightened_t4_dual_stream_join_8_000004")
        self.assertEqual({sample.metadata(config)["measurement_point"] for sample in samples}, {"b_tool_in_loop_repair"})

    def test_baseline_b_t3_t4_smoke_config_targets_repair_knee(self) -> None:
        config = load_runner_config(Path("configs/legacy/sr2fpga_baseline_b_t3_t4_smoke.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.repair_provider, "deepseek")
        self.assertEqual(config.max_attempts, 4)
        self.assertEqual(config.sample_id_prefix, "baseline_b_t3_t4_smoke")
        self.assertEqual([sample.topology_id for sample in samples], ["t3_stream_fork", "t4_dual_stream_join"])
        self.assertEqual(
            [sample.sample_id for sample in samples],
            [
                "sample_baseline_b_t3_t4_smoke_t3_stream_fork_8_000001",
                "sample_baseline_b_t3_t4_smoke_t4_dual_stream_join_8_000002",
            ],
        )
        self.assertEqual({sample.metadata(config)["measurement_point"] for sample in samples}, {"b_tool_in_loop_repair"})

    def test_his_v12_smoke_config_uses_catalog_tier(self) -> None:
        config = load_runner_config(Path("configs/current/sr2fpga_his_v12_smoke.example.yaml"))

        self.assertEqual(planned_samples(config)[0].difficulty_tier, "T2")

    def test_t0_t4_deterministic_smoke_config_covers_task_catalog_once(self) -> None:
        catalog = json.loads(Path("docs/sr2fpga-t0-t4-task-catalog.json").read_text(encoding="utf-8"))
        runtime_catalog = json.loads(Path("docs/sr2fpga-task-catalog-v0.2.json").read_text(encoding="utf-8"))
        catalog_specs = {
            alias: (family["family_id"], family["sr2fpga_tier"])
            for family in runtime_catalog["task_families"]
            for alias in family.get("current_generator_aliases", [])
        }
        config = load_runner_config(Path("configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deterministic")
        self.assertEqual(config.repair_provider, "none")
        self.assertEqual(config.max_attempts, 1)
        self.assertEqual(config.sample_id_prefix, "t0_t4_deterministic_smoke")
        self.assertEqual(len(samples), 24)
        self.assertEqual([sample.source for sample in samples], ["deterministic"] * 24)
        self.assertEqual(
            [(sample.task_type, sample.width) for sample in samples],
            [(entry["task_type"], entry["default_width"]) for entry in catalog["tasks"]],
        )
        self.assertEqual(
            [(sample.family_id, sample.difficulty_tier) for sample in samples],
            [catalog_specs[sample.topology_id or sample.task_type] for sample in samples],
        )
        self.assertEqual({sample.measurement_point for sample in samples}, {"a_first_attempt_no_tools"})
        self.assertEqual({sample.failure_origin for sample in samples}, {"deterministic"})
        self.assertEqual({sample.requirement_style for sample in samples}, {"simple_prompt"})
        self.assertEqual(
            samples[0].requirement,
            "Generate an 8-bit FPGA RTL project that implements a synchronous counter with enable and reset.",
        )
        self.assertNotIn("system_his.json", samples[0].requirement)
        self.assertEqual(
            samples[23].requirement,
            "Generate an 8-bit FPGA RTL project with host transition packetization, indexed replay sample "
            "requests, read/write arbitration, sample packet output, occupancy status, and irq reporting.",
        )
        self.assertNotIn("Preserve these interface contracts", samples[23].requirement)
        self.assertNotIn("replay_request_arbiter", samples[23].requirement)
        self.assertNotIn("->", samples[23].requirement)

        tier_counts: dict[str, int] = {}
        for sample in samples:
            tier_counts[sample.difficulty_tier] = tier_counts.get(sample.difficulty_tier, 0) + 1
        self.assertEqual(tier_counts, {"T0": 6, "T1": 3, "T2": 5, "T3": 5, "T4": 5})

    def test_unvetted_openai_compat_source_is_quarantined(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("/tmp/test"),
            export_root=Path("/tmp/test_exports"),
            run_root=Path("/tmp/test_runs"),
            provider="my_openai",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=False,
            line_b_targets={},
            tasks=[],
            model="gpt-4",
            base_url="https://api.openai.example/v1",
            api_key_env="OPENAI_API_KEY",
            sources={
                "my_openai": SourceConnection(
                    name="my_openai",
                    kind="openai_compat",
                    generation_mode="two_stage",
                )
            },
        )
        sample = PlannedSample(
            sample_id="s1",
            source="my_openai",
            task_type="counter",
            width=8,
            project_name="counter_8",
            requirement="Design a counter.",
        )

        schema = _sample_system_his_schema_version(sample, config)

        self.assertEqual(schema, "system-his-v1.1")
        self.assertEqual(sample.metadata(config)["training_split"], "quarantine")

    def test_unknown_source_kind_fails_preflight_auth_diagnostics(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("/tmp/test"),
            export_root=Path("/tmp/test_exports"),
            run_root=Path("/tmp/test_runs"),
            provider="bad_source",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=False,
            line_b_targets={},
            tasks=[],
            sources={
                "bad_source": SourceConnection(
                    name="bad_source",
                    kind="openai-compat",
                    api_key_env="SOME_KEY",
                    generation_mode="two_stage",
                )
            },
        )
        sample = PlannedSample(
            sample_id="s1",
            source="bad_source",
            task_type="counter",
            width=8,
            project_name="counter_8",
            requirement="Design a counter.",
        )

        _, errors = _source_auth_diagnostics(config, [sample], validate_provider=False)

        self.assertTrue(
            any("unsupported kind" in error for error in errors),
            f"Expected unsupported source kind error, got: {errors}",
        )

    def test_official_eval_gap_closure_config_uses_catalog_tiers(self) -> None:
        config = load_runner_config(Path("configs/current/sr2fpga_official_eval_gap_closure.example.yaml"))

        self.assertEqual(
            {sample.task_type: sample.difficulty_tier for sample in planned_samples(config)},
            {
                "composed_event_counter": "T1",
                "composed_stream_accumulator": "T2",
                "composed_stream_fork": "T2",
                "composed_dual_stream_join": "T2",
                "composed_vector_mac_pipeline": "T3",
                "composed_td_update_core": "T3",
                "composed_policy_value_shell": "T4",
                "composed_replay_sample_shell": "T3",
                "composed_host_protocol_shell": "T4",
                "composed_rl_accelerator_shell": "T4",
                "composed_batch_rl_accelerator_shell": "T4",
                "composed_replay_arbiter_shell": "T4",
                "alu_control_unit": "T1",
                "crc_stream_checker": "T2",
            },
        )

    def test_l0_by_construction_ablation_config_pairs_full_and_skeleton_generation(self) -> None:
        config = load_runner_config(Path("configs/archive/sr2fpga_l0_by_construction_ablation.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.repair_provider, "none")
        self.assertEqual(config.max_attempts, 1)
        self.assertEqual(config.sample_id_prefix, "l0_by_construction_ablation")
        self.assertEqual(len(samples), 8)
        self.assertEqual(
            [sample.topology_id for sample in samples],
            [
                "t1_event_counter",
                "t2_stream_accumulator",
                "t3_stream_fork",
                "t4_dual_stream_join",
                "t1_event_counter",
                "t2_stream_accumulator",
                "t3_stream_fork",
                "t4_dual_stream_join",
            ],
        )
        self.assertEqual({sample.width for sample in samples}, {8})
        self.assertEqual({sample.requirement_style for sample in samples}, {"natural_component"})
        self.assertEqual({sample.metadata(config)["measurement_point"] for sample in samples}, {"a_first_attempt_no_tools"})
        self.assertEqual({sample.metadata(config)["failure_origin"] for sample in samples}, {"natural_llm"})
        self.assertEqual(
            [sample.metadata(config)["contract_skeleton_mode"] for sample in samples],
            [
                "legacy_full_project",
                "legacy_full_project",
                "legacy_full_project",
                "legacy_full_project",
                "behavior_files",
                "behavior_files",
                "behavior_files",
                "behavior_files",
            ],
        )
        self.assertEqual(
            [sample.metadata(config)["system_his_schema_version"] for sample in samples],
            [
                "system-his-v1.1",
                "system-his-v1.1",
                "system-his-v1.1",
                "system-his-v1.1",
                "system-his-v1.2",
                "system-his-v1.2",
                "system-his-v1.2",
                "system-his-v1.2",
            ],
        )

    def test_l0_by_construction_preflight_preview_shows_ablation_arm_metadata(self) -> None:
        config = load_runner_config(Path("configs/archive/sr2fpga_l0_by_construction_ablation.example.yaml"))

        report = runner_preflight(config, run_id="l0-by-construction-ablation")

        self.assertEqual(report["planned_samples"], 8)
        self.assertEqual(
            [sample["contract_skeleton_mode"] for sample in report["samples"]],
            [
                "legacy_full_project",
                "legacy_full_project",
                "legacy_full_project",
                "legacy_full_project",
                "behavior_files",
                "behavior_files",
                "behavior_files",
                "behavior_files",
            ],
        )
        self.assertEqual(
            [sample["system_his_schema_version"] for sample in report["samples"]],
            [
                "system-his-v1.1",
                "system-his-v1.1",
                "system-his-v1.1",
                "system-his-v1.1",
                "system-his-v1.2",
                "system-his-v1.2",
                "system-his-v1.2",
                "system-his-v1.2",
            ],
        )
        self.assertEqual(
            [sample["training_split"] for sample in report["samples"]],
            [
                "quarantine",
                "quarantine",
                "quarantine",
                "quarantine",
                "clean",
                "clean",
                "clean",
                "clean",
            ],
        )

    def test_deterministic_samples_are_v12_clean_training_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            sample = planned_samples(config)[0]

            metadata = sample.metadata(config)

            self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.2")
            self.assertEqual(metadata["training_split"], "clean")
            self.assertEqual(metadata["contract_skeleton_mode"], "deterministic_template")

    def test_load_runner_config_parses_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "env_file": ".env",
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4],
                                "count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertEqual(config.env_file, Path(".env"))

    def test_load_runner_config_rejects_unknown_requirement_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4],
                                "count": 1,
                                "requirement_style": "rewrite_with_llm",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit):
                load_runner_config(config_path)

    def test_simple_prompt_requirement_style_uses_short_user_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "tasks": [
                            {
                                "source": "deepseek-his-v12",
                                "task_type": "component_topology",
                                "topology_ids": ["t4_dual_stream_join"],
                                "widths": [8],
                                "count": 1,
                                "requirement_style": "simple_prompt",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)
            sample = planned_samples(config)[0]

            self.assertEqual(sample.requirement_style, "simple_prompt")
            self.assertEqual(
                sample.requirement,
                "Generate an 8-bit FPGA RTL project that joins two input streams, accumulates joined samples, and exposes one output stream.",
            )
            self.assertNotIn("Preserve these interface contracts", sample.requirement)
            self.assertNotIn("system_his.json", sample.requirement)

    def test_load_runner_config_accepts_finetuned_measurement_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4],
                                "count": 1,
                                "measurement_point": "c_finetuned_first_attempt_no_tools",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertEqual(config.tasks[0].measurement_point, "c_finetuned_first_attempt_no_tools")

    def test_load_runner_config_rejects_unknown_measurement_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4],
                                "count": 1,
                                "measurement_point": "typo_measurement",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit):
                load_runner_config(config_path)

    def test_load_runner_config_parses_component_topology_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "component_topology",
                                "topology_ids": ["t1_event_counter", "t2_stream_accumulator"],
                                "widths": [8],
                                "count": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertEqual(config.tasks[0].topology_ids, ["t1_event_counter", "t2_stream_accumulator"])

    def test_catalog_tier_overrides_legacy_yaml_difficulty_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets",
                        "export_root": "exports",
                        "run_root": "runs",
                        "tasks": [
                            {
                                "task_type": "counter",
                                "difficulty_tier": "T2",
                                "widths": [8],
                                "count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertEqual(config.tasks[0].difficulty_tier, "T2")
            self.assertEqual(planned_samples(config)[0].difficulty_tier, "T0")

    def test_load_baseline_a_example_config_targets_first_attempt_no_tools(self) -> None:
        config_path = Path(__file__).resolve().parents[2] / "configs" / "legacy" / "sr2fpga_baseline_a.example.yaml"

        config = load_runner_config(config_path)
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.repair_provider, "none")
        self.assertEqual(config.max_attempts, 1)
        self.assertEqual(config.tasks[0].requirement_style, "natural_component")
        self.assertEqual([sample.metadata(config)["measurement_point"] for sample in samples], [
            "a_first_attempt_no_tools",
            "a_first_attempt_no_tools",
            "a_first_attempt_no_tools",
            "a_first_attempt_no_tools",
        ])
        self.assertEqual([sample.metadata(config)["failure_origin"] for sample in samples], [
            "natural_llm",
            "natural_llm",
            "natural_llm",
            "natural_llm",
        ])
        self.assertEqual([sample.metadata(config)["requirement_style"] for sample in samples], [
            "natural_component",
            "natural_component",
            "natural_component",
            "natural_component",
        ])
        self.assertEqual(
            [(sample.source, sample.task_type, sample.topology_id, sample.difficulty_tier) for sample in samples],
            [
                ("deepseek", "composed_event_counter", "t1_event_counter", "T1"),
                ("deepseek", "composed_stream_accumulator", "t2_stream_accumulator", "T2"),
                ("deepseek", "composed_stream_fork", "t3_stream_fork", "T2"),
                ("deepseek", "composed_dual_stream_join", "t4_dual_stream_join", "T2"),
            ],
        )

    def test_runner_preflight_reports_missing_api_key_and_existing_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "baseline_a"
            run_dir.mkdir(parents=True)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deepseek",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1)],
                api_key_env="DEEPSEEK_API_KEY",
            )

            with (
                patch.dict(os.environ, {}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
            ):
                report = runner_preflight(config, run_id="baseline_a")

            self.assertFalse(report["ok"])
            self.assertIn("DEEPSEEK_API_KEY is not set for source deepseek", report["errors"])
            self.assertIn("run directory already exists: " + str(run_dir), report["warnings"])
            self.assertEqual(report["planned_samples"], 1)
            self.assertEqual(
                report["samples"],
                [
                    {
                        "sample_id": "sample_runner_counter_4_000001",
                        "source": "deepseek",
                        "task_type": "counter",
                        "family_id": "binary_bcd_counter",
                        "width": 4,
                        "requirement_style": "contract",
                        "requirement": (
                            "Design a 4-bit counter as a complete SR2FPGA Verilog RTL project. "
                            "Use multi-file RTL for FIFO, SPI, UART, PWM, and controller-style tasks; "
                            "include system_his.json, manifest.json, timing constraints, a bounded "
                            "self-checking testbench that prints TEST_PASS on success or TEST_FAIL on "
                            "failure, and predicted QoR."
                        ),
                        "difficulty_tier": "T0",
                        "topology_id": "",
                        "failure_origin": "natural_llm",
                        "measurement_point": "a_first_attempt_no_tools",
                        "evaluation_line": "line_b",
                        "system_his_schema_version": "system-his-v1.1",
                        "training_split": "quarantine",
                        "contract_skeleton_mode": "legacy_full_project",
                    }
                ],
            )

    def test_runner_preflight_loads_api_key_from_env_file_without_reporting_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / ".env"
            env_path.write_text("DEEPSEEK_API_KEY=fake-test-key\n", encoding="utf-8")
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deepseek",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1)],
                api_key_env="DEEPSEEK_API_KEY",
                env_file=env_path,
            )

            with (
                patch.dict(os.environ, {}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
            ):
                report = runner_preflight(config, run_id="env_file_preflight")

            self.assertTrue(report["ok"])
            self.assertEqual(report["env_file"], str(env_path))
            self.assertEqual(report["api_keys"]["DEEPSEEK_API_KEY"]["source"], str(env_path))
            self.assertTrue(report["api_keys"]["DEEPSEEK_API_KEY"]["present"])
            self.assertRegex(report["api_keys"]["DEEPSEEK_API_KEY"]["fingerprint"], r"^[0-9a-f]{8}$")
            self.assertNotIn("fake-test-key", json.dumps(report))

    def test_runner_preflight_reports_missing_api_key_for_deepseek_his_v12_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek-his-v12", task_type="counter", widths=[4], count=1)],
                api_key_env="DEEPSEEK_API_KEY",
            )

            with (
                patch.dict(os.environ, {}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
            ):
                report = runner_preflight(config, run_id="his_v12_preflight")

            self.assertFalse(report["ok"])
            self.assertIn("DEEPSEEK_API_KEY is not set for source deepseek-his-v12", report["errors"])
            self.assertIn("deepseek-his-v12", report["providers"])

    def test_runner_preflight_reports_shell_api_key_source_without_reporting_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deepseek",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1)],
                api_key_env="DEEPSEEK_API_KEY",
            )

            with (
                patch.dict(os.environ, {"DEEPSEEK_API_KEY": "shell-fake-key"}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
            ):
                report = runner_preflight(config, run_id="shell_key_preflight")

            self.assertTrue(report["ok"])
            self.assertEqual(report["api_keys"]["DEEPSEEK_API_KEY"]["source"], "environment")
            self.assertTrue(report["api_keys"]["DEEPSEEK_API_KEY"]["present"])
            self.assertNotIn("shell-fake-key", json.dumps(report))

    def test_runner_preflight_validate_provider_reports_deepseek_auth_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deepseek",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1)],
                api_key_env="DEEPSEEK_API_KEY",
            )

            with (
                patch.dict(os.environ, {"DEEPSEEK_API_KEY": "shell-fake-key"}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
                patch("LLM.src.sr2fpga_agent.runner.OpenAICompatibleClient") as client_cls,
            ):
                client_cls.return_value.chat.return_value = '{"ok": true}'
                report = runner_preflight(config, run_id="auth_ok", validate_provider=True)

            self.assertTrue(report["ok"])
            self.assertEqual(report["provider_auth"]["deepseek"]["status"], "ok")
            self.assertNotIn("shell-fake-key", json.dumps(report))

    def test_runner_preflight_validate_provider_uses_wider_auth_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="gpt55", task_type="counter", widths=[4], count=1)],
                sources={
                    "gpt55": SourceConnection(
                        name="gpt55",
                        kind="openai_compat",
                        model="gpt-5.5",
                        base_url="https://example/v1",
                        api_key_env="OPENAI_API_KEY",
                        generation_mode="two_stage",
                        timeout_seconds=900,
                    )
                },
            )

            with (
                patch.dict(os.environ, {"OPENAI_API_KEY": "shell-fake-key"}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
                patch("LLM.src.sr2fpga_agent.runner.OpenAICompatibleClient") as client_cls,
            ):
                client_cls.return_value.chat.return_value = '{"ok": true}'
                report = runner_preflight(config, run_id="auth_ok", validate_provider=True)

            self.assertTrue(report["ok"])
            client_config = client_cls.call_args.args[0]
            self.assertEqual(client_config.timeout_seconds, 120)

    def test_runner_preflight_validate_provider_uses_anthropic_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="claude", task_type="counter", widths=[4], count=1)],
                sources={
                    "claude": SourceConnection(
                        name="claude",
                        kind="anthropic_compat",
                        model="claude-opus-4-8",
                        base_url="https://w.ciykj.cn/v1",
                        api_key_env="ANTHROPIC_API_KEY",
                        generation_mode="two_stage",
                        timeout_seconds=900,
                    )
                },
            )

            with (
                patch.dict(os.environ, {"ANTHROPIC_API_KEY": "shell-fake-key"}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
                patch("LLM.src.sr2fpga_agent.runner.AnthropicCompatibleClient") as client_cls,
            ):
                client_cls.return_value.chat.return_value = '{"ok": true}'
                report = runner_preflight(config, run_id="auth_ok", validate_provider=True)

            self.assertTrue(report["ok"])
            client_config = client_cls.call_args.args[0]
            self.assertEqual(client_config.base_url, "https://w.ciykj.cn/v1")
            self.assertEqual(client_config.api_key, "shell-fake-key")
            self.assertEqual(client_config.timeout_seconds, 120)

    def test_run_batch_accepts_named_source_repair_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="claude-repair",
                max_attempts=2,
                refresh_exports=False,
                line_b_targets={},
                tasks=[],
                sources={
                    "claude-repair": SourceConnection(
                        name="claude-repair",
                        kind="anthropic_compat",
                        model="claude-opus-4-8",
                        base_url="https://w.ciykj.cn/v1",
                        api_key_env="ANTHROPIC_API_KEY",
                        generation_mode="two_stage",
                    )
                },
            )

            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "shell-fake-key"}, clear=False):
                summary = run_batch(config, run_id="named_repair")

            self.assertEqual(summary["total_planned"], 0)
            self.assertEqual(summary["total_completed"], 0)

    def test_runner_preflight_validate_provider_reports_deepseek_auth_failure_without_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deepseek",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1)],
                api_key_env="DEEPSEEK_API_KEY",
            )

            with (
                patch.dict(os.environ, {"DEEPSEEK_API_KEY": "shell-fake-key"}, clear=True),
                patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
                patch("LLM.src.sr2fpga_agent.runner.OpenAICompatibleClient") as client_cls,
            ):
                client_cls.return_value.chat.side_effect = RuntimeError("auth failed for shell-fake-key")
                report = runner_preflight(config, run_id="auth_fail", validate_provider=True)

            self.assertFalse(report["ok"])
            self.assertEqual(report["provider_auth"]["deepseek"]["status"], "failed")
            self.assertIn("deepseek provider auth failed", report["errors"])
            self.assertNotIn("shell-fake-key", json.dumps(report))

    def test_runner_preflight_passes_for_deterministic_no_network_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )

            with patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"):
                report = runner_preflight(config, run_id="deterministic_smoke")

            self.assertTrue(report["ok"])
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["planned_samples"], 1)
            self.assertEqual(report["tools"]["verilator"], "found")
            self.assertEqual(report["samples"][0]["sample_id"], "sample_runner_counter_4_000001")
            self.assertEqual(report["samples"][0]["family_id"], "binary_bcd_counter")

    def test_baseline_a_preflight_sample_preview_lists_t1_to_t4_topologies(self) -> None:
        config_path = Path(__file__).resolve().parents[2] / "configs" / "legacy" / "sr2fpga_baseline_a.example.yaml"
        config = load_runner_config(config_path)

        with (
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "set-for-test"}),
            patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"),
        ):
            report = runner_preflight(config, run_id="deepseek-baseline-a")

        self.assertTrue(report["ok"])
        self.assertEqual(
            [(item["task_type"], item["topology_id"], item["difficulty_tier"]) for item in report["samples"]],
            [
                ("composed_event_counter", "t1_event_counter", "T1"),
                ("composed_stream_accumulator", "t2_stream_accumulator", "T2"),
                ("composed_stream_fork", "t3_stream_fork", "T2"),
                ("composed_dual_stream_join", "t4_dual_stream_join", "T2"),
            ],
        )
        t4_requirement = report["samples"][3]["requirement"]
        self.assertEqual(report["samples"][3]["requirement_style"], "natural_component")
        self.assertIn("Build an 8-bit dual-stream join datapath", t4_requirement)
        self.assertIn("t4_dual_stream_join", t4_requirement)
        self.assertIn("difficulty tier T2", t4_requirement)
        self.assertIn("skid_buffer", t4_requirement)
        self.assertIn("stream_join", t4_requirement)
        self.assertIn("accumulator_core", t4_requirement)
        self.assertIn("stream_stage", t4_requirement)
        self.assertIn("top.in0_valid -> skid_buffer.in_valid", t4_requirement)
        self.assertIn("stream_join.out_valid -> accumulator_core.sample_valid", t4_requirement)
        self.assertIn("two valid-ready input streams", t4_requirement)
        self.assertNotIn("Instantiate nodes", t4_requirement)
        self.assertNotIn("Wire required edges", t4_requirement)

    def test_load_runner_config_rejects_non_mapping_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(json.dumps(["not", "a", "mapping"]), encoding="utf-8")

            with self.assertRaises(SystemExit):
                load_runner_config(config_path)

    def test_load_runner_config_rejects_empty_widths_for_positive_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [],
                                "count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit):
                load_runner_config(config_path)

    def test_load_runner_config_parses_false_refresh_exports_string(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "refresh_exports": "false",
                        "tasks": [],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertFalse(config.refresh_exports)

    def test_planned_samples_expand_widths_and_counts(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets/sr2fpga_rtl_v1"),
            export_root=Path("datasets/sr2fpga_rtl_v1_exports"),
            run_root=Path("tmp/sr2fpga_runs"),
            provider="deterministic",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=True,
            line_b_targets={"l3_success_ratio": 0.4, "repair_trajectory_ratio": 0.6, "max_samples": 4},
            tasks=[
                TaskConfig(source="deterministic", task_type="counter", widths=[4, 8], count=2),
                TaskConfig(source="deterministic", task_type="fifo", widths=[8], count=1),
            ],
        )

        samples = planned_samples(config)

        self.assertEqual(
            [(item.sample_id, item.task_type, item.width, item.project_name) for item in samples],
            [
                ("sample_runner_counter_4_000001", "counter", 4, "runner_counter_4_000001"),
                ("sample_runner_counter_8_000002", "counter", 8, "runner_counter_8_000002"),
                ("sample_runner_fifo_8_000003", "fifo", 8, "runner_fifo_8_000003"),
            ],
        )

    def test_planned_samples_resolve_direct_catalog_family_identity_and_tier(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets/sr2fpga_rtl_v1"),
            export_root=Path("datasets/sr2fpga_rtl_v1_exports"),
            run_root=Path("tmp/sr2fpga_runs"),
            provider="deterministic",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=True,
            line_b_targets={"max_samples": 3},
            tasks=[
                TaskConfig(source="deterministic", task_type="fir_filter", widths=[8], count=1),
                TaskConfig(source="deterministic", task_type="spi_master", widths=[8], count=1),
                TaskConfig(source="deterministic", task_type="matrix_vector_mac", widths=[8], count=1),
            ],
        )

        samples = planned_samples(config)

        self.assertEqual(
            [(sample.task_type, sample.family_id, sample.difficulty_tier) for sample in samples],
            [
                ("fir_filter", "fir_filter", "T3"),
                ("spi_master", "spi_master", "T1"),
                ("matrix_vector_mac", "matrix_vector_mac", "T3"),
            ],
        )
        self.assertEqual(samples[0].metadata(config)["family_id"], "fir_filter")

    def test_planned_samples_cycle_widths_and_respect_max_samples(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets/sr2fpga_rtl_v1"),
            export_root=Path("datasets/sr2fpga_rtl_v1_exports"),
            run_root=Path("tmp/sr2fpga_runs"),
            provider="deterministic",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=True,
            line_b_targets={"max_samples": 3},
            tasks=[
                TaskConfig(source="deterministic", task_type="counter", widths=[4, 8], count=5),
            ],
        )

        samples = planned_samples(config)

        self.assertEqual([item.width for item in samples], [4, 8, 4])

    def test_planned_samples_include_reframe_metadata_defaults(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets/sr2fpga_rtl_v1"),
            export_root=Path("datasets/sr2fpga_rtl_v1_exports"),
            run_root=Path("tmp/sr2fpga_runs"),
            provider="deterministic",
            repair_provider="deepseek",
            max_attempts=2,
            refresh_exports=True,
            line_b_targets={"max_samples": 2},
            tasks=[
                TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1),
                TaskConfig(
                    source="deterministic",
                    task_type="counter",
                    widths=[4],
                    count=1,
                    failure_injectors=["wrong_top_module"],
                ),
            ],
        )

        samples = planned_samples(config)

        self.assertEqual(samples[0].metadata(config)["generator_provider"], "deepseek")
        self.assertEqual(samples[0].metadata(config)["failure_origin"], "natural_llm")
        self.assertEqual(samples[0].metadata(config)["difficulty_tier"], "T0")
        self.assertEqual(samples[0].metadata(config)["measurement_point"], "b_tool_in_loop_repair")
        self.assertEqual(samples[0].metadata(config)["contract_skeleton_mode"], "legacy_full_project")
        self.assertEqual(samples[1].metadata(config)["failure_origin"], "synthetic_injected")
        self.assertEqual(samples[1].metadata(config)["contract_skeleton_mode"], "deterministic_template")

    def test_planned_samples_allow_task_measurement_point_override(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets/sr2fpga_rtl_v1"),
            export_root=Path("datasets/sr2fpga_rtl_v1_exports"),
            run_root=Path("tmp/sr2fpga_runs"),
            provider="deterministic",
            repair_provider="deepseek",
            max_attempts=4,
            refresh_exports=True,
            line_b_targets={"max_samples": 1},
            tasks=[
                TaskConfig(
                    source="deepseek",
                    task_type="uart_tx",
                    widths=[8],
                    count=1,
                    failure_origin="natural_llm",
                    measurement_point="a_first_attempt_no_tools",
                )
            ],
        )

        sample = planned_samples(config)[0]

        self.assertEqual(sample.metadata(config)["measurement_point"], "a_first_attempt_no_tools")

    def test_planned_samples_expand_component_topology_ids(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets/sr2fpga_rtl_v1"),
            export_root=Path("datasets/sr2fpga_rtl_v1_exports"),
            run_root=Path("tmp/sr2fpga_runs"),
            provider="deterministic",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=True,
            line_b_targets={"max_samples": 12},
            tasks=[
                TaskConfig(
                    source="deterministic",
                    task_type="component_topology",
                    widths=[8],
                    count=12,
                    topology_ids=[
                        "t1_event_counter",
                        "t2_stream_accumulator",
                        "t3_stream_fork",
                        "t4_dual_stream_join",
                        "t5_vector_mac_pipeline",
                        "t6_td_update_core",
                        "t7_policy_value_shell",
                        "t8_replay_sample_shell",
                        "t9_host_protocol_shell",
                        "t10_rl_accelerator_shell",
                        "t11_batch_rl_accelerator_shell",
                        "t12_replay_arbiter_shell",
                    ],
                    failure_origin="compositional_assembly",
                )
            ],
        )

        samples = planned_samples(config)

        self.assertEqual(
            [(item.sample_id, item.task_type, item.topology_id, item.family_id, item.difficulty_tier) for item in samples],
            [
                ("sample_runner_t1_event_counter_8_000001", "composed_event_counter", "t1_event_counter", "t1_event_counter", "T1"),
                (
                    "sample_runner_t2_stream_accumulator_8_000002",
                    "composed_stream_accumulator",
                    "t2_stream_accumulator",
                    "valid_ready_stream_accumulator",
                    "T2",
                ),
                ("sample_runner_t3_stream_fork_8_000003", "composed_stream_fork", "t3_stream_fork", "stream_fork_join", "T2"),
                (
                    "sample_runner_t4_dual_stream_join_8_000004",
                    "composed_dual_stream_join",
                    "t4_dual_stream_join",
                    "stream_fork_join",
                    "T2",
                ),
                (
                    "sample_runner_t5_vector_mac_pipeline_8_000005",
                    "composed_vector_mac_pipeline",
                    "t5_vector_mac_pipeline",
                    "mac_array",
                    "T3",
                ),
                (
                    "sample_runner_t6_td_update_core_8_000006",
                    "composed_td_update_core",
                    "t6_td_update_core",
                    "qtable_update_core",
                    "T3",
                ),
                (
                    "sample_runner_t7_policy_value_shell_8_000007",
                    "composed_policy_value_shell",
                    "t7_policy_value_shell",
                    "rl_reward_policy_update",
                    "T4",
                ),
                (
                    "sample_runner_t8_replay_sample_shell_8_000008",
                    "composed_replay_sample_shell",
                    "t8_replay_sample_shell",
                    "t8_replay_sample_shell",
                    "T3",
                ),
                (
                    "sample_runner_t9_host_protocol_shell_8_000009",
                    "composed_host_protocol_shell",
                    "t9_host_protocol_shell",
                    "t9_host_protocol_shell",
                    "T4",
                ),
                (
                    "sample_runner_t10_rl_accelerator_shell_8_000010",
                    "composed_rl_accelerator_shell",
                    "t10_rl_accelerator_shell",
                    "p_rl_qlearning_accel",
                    "T4",
                ),
                (
                    "sample_runner_t11_batch_rl_accelerator_shell_8_000011",
                    "composed_batch_rl_accelerator_shell",
                    "t11_batch_rl_accelerator_shell",
                    "p_rl_qlearning_accel",
                    "T4",
                ),
                (
                    "sample_runner_t12_replay_arbiter_shell_8_000012",
                    "composed_replay_arbiter_shell",
                    "t12_replay_arbiter_shell",
                    "t12_replay_arbiter_shell",
                    "T4",
                ),
            ],
        )
        self.assertEqual(samples[0].metadata(config)["topology_id"], "t1_event_counter")
        self.assertEqual(samples[1].metadata(config)["topology_id"], "t2_stream_accumulator")
        self.assertEqual(samples[2].metadata(config)["topology_id"], "t3_stream_fork")
        self.assertEqual(samples[3].metadata(config)["topology_id"], "t4_dual_stream_join")
        self.assertEqual(samples[4].metadata(config)["topology_id"], "t5_vector_mac_pipeline")
        self.assertEqual(samples[5].metadata(config)["topology_id"], "t6_td_update_core")
        self.assertEqual(samples[6].metadata(config)["topology_id"], "t7_policy_value_shell")
        self.assertEqual(samples[7].metadata(config)["topology_id"], "t8_replay_sample_shell")
        self.assertEqual(samples[8].metadata(config)["topology_id"], "t9_host_protocol_shell")
        self.assertEqual(samples[9].metadata(config)["topology_id"], "t10_rl_accelerator_shell")
        self.assertEqual(samples[10].metadata(config)["topology_id"], "t11_batch_rl_accelerator_shell")
        self.assertEqual(samples[11].metadata(config)["topology_id"], "t12_replay_arbiter_shell")
        self.assertEqual(samples[3].metadata(config)["requirement_style"], "contract")
        self.assertIn("component topology t1_event_counter", samples[0].requirement)
        self.assertIn("event_gate", samples[0].requirement)
        self.assertIn("counter_core", samples[0].requirement)
        self.assertIn("event_valid pulses", samples[0].requirement)
        self.assertIn("component topology t4_dual_stream_join", samples[3].requirement)
        self.assertIn("skid_a:skid_buffer", samples[3].requirement)
        self.assertIn("skid_b:skid_buffer", samples[3].requirement)
        self.assertIn("stream_join.out_data -> accumulator_core.sample", samples[3].requirement)
        self.assertIn("component topology t5_vector_mac_pipeline", samples[4].requirement)
        self.assertIn("vector_mac_core", samples[4].requirement)
        self.assertIn("component topology t6_td_update_core", samples[5].requirement)
        self.assertIn("td_update_core", samples[5].requirement)
        self.assertIn("component topology t7_policy_value_shell", samples[6].requirement)
        self.assertIn("action_select_core", samples[6].requirement)
        self.assertIn("component topology t8_replay_sample_shell", samples[7].requirement)
        self.assertIn("replay_store", samples[7].requirement)
        self.assertIn("component topology t9_host_protocol_shell", samples[8].requirement)
        self.assertIn("axi_lite_write_ctrl", samples[8].requirement)
        self.assertIn("component topology t10_rl_accelerator_shell", samples[9].requirement)
        self.assertIn("policy_value_core", samples[9].requirement)
        self.assertIn("td_update_core", samples[9].requirement)
        self.assertIn("component topology t11_batch_rl_accelerator_shell", samples[10].requirement)
        self.assertIn("dual_policy_value_core", samples[10].requirement)
        self.assertIn("dual_td_update_core", samples[10].requirement)
        self.assertIn("component topology t12_replay_arbiter_shell", samples[11].requirement)
        self.assertIn("replay_request_arbiter", samples[11].requirement)
        self.assertIn("replay_memory_bank", samples[11].requirement)
        self.assertIn("Keep rtl/top.v as the integration wrapper", samples[3].requirement)

    def test_classify_sample_bucket(self) -> None:
        self.assertEqual(classify_sample_bucket({"pass_level": "L3", "failure_count": 0}), "success_l3")
        self.assertEqual(classify_sample_bucket({"pass_level": "L4", "failure_count": 0}), "success_l3")
        self.assertEqual(classify_sample_bucket({"pass_level": "L1", "failure_count": 2}), "repair_trajectory")
        self.assertEqual(classify_sample_bucket({"pass_level": "GEN_FAIL", "failure_count": 1}), "rejected")
        self.assertEqual(classify_sample_bucket({"pass_level": "L0", "failure_count": 0}), "rejected")

    def test_generation_failures_have_dedicated_failure_family(self) -> None:
        self.assertEqual(_failure_family("generation_failed", "generation"), "generation_failure")

    def test_repair_failures_have_dedicated_failure_family(self) -> None:
        self.assertEqual(_failure_family("repair_failed", "repair"), "repair_failure")

    def test_testbench_static_check_has_dedicated_failure_family(self) -> None:
        self.assertEqual(_failure_family("testbench_observation_race", "testbench_static_check"), "testbench_failure")
        self.assertEqual(
            _failure_family("testbench_stimulus_reaccept_risk", "testbench_static_check"),
            "testbench_failure",
        )
        self.assertEqual(
            _failure_family("testbench_missing_functional_oracle", "testbench_static_check"),
            "testbench_failure",
        )
        self.assertEqual(_failure_family("testbench_missing_functional_oracle"), "testbench_failure")
        self.assertEqual(_failure_family("testbench_internal_signal_access"), "testbench_failure")

    def test_initial_run_state_defaults(self) -> None:
        state = initial_run_state("run_test", config_fingerprint="abc123")

        self.assertEqual(state.run_id, "run_test")
        self.assertEqual(state.config_fingerprint, "abc123")
        self.assertEqual(state.next_index, 0)
        self.assertEqual(state.completed_samples, [])
        self.assertEqual(state.buckets, {"success_l3": [], "repair_trajectory": [], "rejected": []})
        self.assertEqual(state.failure_types, {})
        self.assertFalse(state.exports_refreshed)

    def test_run_state_round_trip_and_skip_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "run_state.json"
            state = RunState(
                run_id="run_test",
                next_index=1,
                completed_samples=["sample_runner_counter_4_000001"],
                buckets={"success_l3": ["sample_runner_counter_4_000001"], "repair_trajectory": [], "rejected": []},
                failure_types={},
                exports_refreshed=False,
                config_fingerprint="f" * 64,
            )

            write_run_state(state_path, state)
            self.assertTrue(state_path.read_text(encoding="utf-8").endswith("\n"))
            loaded = read_run_state(state_path)

            self.assertEqual(loaded.run_id, "run_test")
            self.assertEqual(loaded.config_fingerprint, "f" * 64)
            self.assertEqual(loaded.next_index, 1)
            self.assertEqual(loaded.completed_samples, ["sample_runner_counter_4_000001"])
            self.assertTrue(should_skip_sample(loaded, "sample_runner_counter_4_000001"))
            self.assertFalse(should_skip_sample(loaded, "sample_runner_counter_8_000002"))

    def test_run_batch_records_samples_summary_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=True,
                line_b_targets={"l3_success_ratio": 0.4, "repair_trajectory_ratio": 0.6, "max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )

            summary = run_batch(config, run_id="run_unit")

            run_dir = root / "runs" / "run_unit"
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            state = read_run_state(run_dir / "run_state.json")
            self.assertEqual(summary["run_id"], "run_unit")
            self.assertRegex(summary["config_fingerprint"], r"^[0-9a-f]{64}$")
            self.assertEqual(state.config_fingerprint, summary["config_fingerprint"])
            self.assertEqual(summary["total_completed"], 1)
            self.assertEqual(summary["next_index"], 1)
            self.assertEqual(summary["buckets"]["success_l3"], ["sample_runner_counter_4_000001"])
            self.assertEqual(summary["metadata_breakdown"]["source"]["deterministic"], 1)
            self.assertEqual(summary["metadata_breakdown"]["failure_origin"]["deterministic_template"], 1)
            self.assertEqual(summary["metadata_breakdown"]["difficulty_tier"]["T0"], 1)
            self.assertEqual(summary["metadata_breakdown"]["contract_skeleton_mode"]["deterministic_template"], 1)
            self.assertEqual(summary["pass_level_breakdown"]["L3"], 1)
            self.assertEqual(
                summary["contract_metrics"],
                {
                    "total_labeled": 1,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            )
            self.assertEqual(summary["failure_family_breakdown"], {})
            self.assertEqual(state.next_index, 1)
            self.assertEqual(
                events,
                [
                    {
                        "event": "sample_completed",
                        "sample_id": "sample_runner_counter_4_000001",
                        "source": "deterministic",
                        "failure_origin": "deterministic_template",
                        "difficulty_tier": "T0",
                        "task_type": "counter",
                        "width": 4,
                        "pass_level": "L3",
                        "bucket": "success_l3",
                    }
                ],
            )
            self.assertTrue((run_dir / "run_state.json").exists())
            self.assertTrue((run_dir / "summary.json").exists())
            self.assertTrue((run_dir / "baseline_report.md").exists())
            baseline_report = (run_dir / "baseline_report.md").read_text(encoding="utf-8")
            self.assertIn("# SR2FPGA Baseline Report: run_unit", baseline_report)
            self.assertIn("| difficulty_tier | T0 | 1 | L3:1 | 100.0% | 0 | 0.0% |", baseline_report)
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((root / "datasets/sample_runner_counter_4_000001/eval/labels.json").exists())
            metadata = json.loads(
                (root / "datasets/sample_runner_counter_4_000001/metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["failure_origin"], "deterministic_template")
            self.assertEqual(metadata["measurement_point"], "a_first_attempt_no_tools")
            self.assertEqual(metadata["contract_skeleton_mode"], "deterministic_template")
            self.assertTrue((root / "exports/requirement_to_project.jsonl").exists())

    def test_run_batch_summary_groups_component_topology_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 2},
                tasks=[
                    TaskConfig(
                        source="deterministic",
                        task_type="component_topology",
                        widths=[8],
                        count=2,
                        topology_ids=["t1_event_counter", "t2_stream_accumulator"],
                        failure_origin="compositional_assembly",
                    )
                ],
            )

            summary = run_batch(config, run_id="run_unit")

            self.assertEqual(summary["metadata_breakdown"]["source"], {"deterministic": 2})
            self.assertEqual(summary["metadata_breakdown"]["failure_origin"], {"compositional_assembly": 2})
            self.assertEqual(summary["metadata_breakdown"]["measurement_point"], {"a_first_attempt_no_tools": 2})
            self.assertEqual(summary["metadata_breakdown"]["requirement_style"], {"contract": 2})
            self.assertEqual(summary["metadata_breakdown"]["contract_skeleton_mode"], {"deterministic_template": 2})
            self.assertEqual(summary["metadata_breakdown"]["difficulty_tier"], {"T1": 1, "T2": 1})
            self.assertEqual(
                summary["metadata_breakdown"]["topology_id"],
                {"t1_event_counter": 1, "t2_stream_accumulator": 1},
            )
            self.assertEqual(summary["pass_level_breakdown"], {"L3": 2})
            self.assertEqual(
                summary["calibration_matrix"]["difficulty_tier"]["T1"],
                {
                    "total": 1,
                    "pass_levels": {"L3": 1},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            )
            self.assertEqual(
                summary["calibration_matrix"]["difficulty_tier"]["T2"],
                {
                    "total": 1,
                    "pass_levels": {"L3": 1},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            )
            self.assertEqual(
                summary["calibration_matrix"]["topology_id"]["t1_event_counter"],
                {
                    "total": 1,
                    "pass_levels": {"L3": 1},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            )
            self.assertEqual(
                summary["calibration_matrix"]["measurement_point"]["a_first_attempt_no_tools"],
                {
                    "total": 2,
                    "pass_levels": {"L3": 2},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            )
            self.assertEqual(
                summary["calibration_matrix"]["requirement_style"]["contract"],
                {
                    "total": 2,
                    "pass_levels": {"L3": 2},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            )
            self.assertEqual(
                summary["calibration_matrix"]["contract_skeleton_mode"]["deterministic_template"],
                {
                    "total": 2,
                    "pass_levels": {"L3": 2},
                    "l3_pass_rate": 1.0,
                    "l0_contract_failures": 0,
                    "cross_file_consistency_error_rate": 0.0,
                },
            )

    def test_run_batch_builds_generator_from_each_task_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1)],
            )

            with patch(
                "LLM.src.sr2fpga_agent.runner.build_project_generator_for_connection"
            ) as build_generator:
                build_generator.return_value = None
                run_batch(config, run_id="run_unit")

            self.assertEqual(build_generator.call_args.args[0].name, "deepseek")

    def test_run_batch_writes_two_stage_generation_events(self) -> None:
        from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deepseek-his-v12",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deepseek-his-v12", task_type="counter", widths=[4], count=1)],
            )

            def fake_build_project_generator(connection, event_sink=None):
                class FakeTwoStageGenerator:
                    def generate(self, request, platform):
                        event_sink(
                            {
                                "event": "generation_stage_started",
                                "stage": "req2his",
                                "project_name": request.project_name,
                                "task_type": request.task_type,
                                "width": request.width,
                            }
                        )
                        event_sink(
                            {
                                "event": "generation_stage_finished",
                                "stage": "req2his",
                                "project_name": request.project_name,
                                "task_type": request.task_type,
                                "width": request.width,
                                "duration_seconds": 0.01,
                            }
                        )
                        return ProjectGenerator().generate(request, platform)

                return FakeTwoStageGenerator()

            with patch(
                "LLM.src.sr2fpga_agent.runner.build_project_generator_for_connection",
                side_effect=fake_build_project_generator,
            ):
                run_batch(config, run_id="run_unit")

            events = [
                json.loads(line)
                for line in (root / "runs" / "run_unit" / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(events[0]["event"], "generation_stage_started")
            self.assertEqual(events[0]["sample_id"], "sample_runner_counter_4_000001")
            self.assertEqual(events[0]["stage"], "req2his")
            self.assertEqual(events[1]["event"], "generation_stage_finished")
            self.assertEqual(events[-1]["event"], "sample_completed")

    def test_run_batch_records_existing_sample_rejection_and_advances_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "datasets/sample_runner_counter_4_000001").mkdir(parents=True)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )

            summary = run_batch(config, run_id="run_unit")
            state = read_run_state(root / "runs" / "run_unit" / "run_state.json")
            events = [
                json.loads(line)
                for line in (root / "runs" / "run_unit" / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(summary["next_index"], 1)
            self.assertEqual(state.next_index, 1)
            self.assertEqual(state.buckets["rejected"], ["sample_runner_counter_4_000001"])
            self.assertEqual(state.failure_types["sample_exists"], 1)
            self.assertEqual(
                events,
                [{"event": "sample_exists", "sample_id": "sample_runner_counter_4_000001"}],
            )

    def test_run_batch_resume_does_not_duplicate_completed_state_or_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )

            first_summary = run_batch(config, run_id="run_unit")
            second_summary = run_batch(config, run_id="run_unit", resume=True)
            state = read_run_state(root / "runs" / "run_unit" / "run_state.json")
            events = [
                json.loads(line)
                for line in (root / "runs" / "run_unit" / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(first_summary["total_completed"], 1)
            self.assertEqual(second_summary["total_completed"], 1)
            self.assertEqual(state.completed_samples, ["sample_runner_counter_4_000001"])
            self.assertEqual(state.buckets["success_l3"], ["sample_runner_counter_4_000001"])
            self.assertEqual(state.failure_types, {})
            self.assertEqual(len(events), 1)

    def test_run_batch_rejects_resume_when_config_fingerprint_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            changed_config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[8], count=1)],
            )

            run_batch(config, run_id="run_unit")
            config_path = root / "runs" / "run_unit" / "config.json"
            original_config_json = config_path.read_text(encoding="utf-8")

            with self.assertRaises(SystemExit):
                run_batch(changed_config, run_id="run_unit", resume=True)

            self.assertEqual(config_path.read_text(encoding="utf-8"), original_config_json)

    def test_run_batch_applies_configured_failure_injectors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[
                    TaskConfig(
                        source="deterministic",
                        task_type="counter",
                        widths=[4],
                        count=1,
                        failure_injectors=["wrong_top_module"],
                    )
                ],
            )

            summary = run_batch(config, run_id="run_unit")

            sample_dir = root / "datasets/sample_runner_counter_4_000001"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads(
                (sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8")
            )

            self.assertEqual(summary["buckets"]["repair_trajectory"], ["sample_runner_counter_4_000001"])
            self.assertEqual(
                summary["contract_metrics"],
                {
                    "total_labeled": 1,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 1.0,
                },
            )
            self.assertEqual(
                summary["calibration_matrix"]["failure_origin"]["synthetic_injected"],
                {
                    "total": 1,
                    "pass_levels": {"L0_FAIL": 1},
                    "l3_pass_rate": 0.0,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 1.0,
                },
            )
            self.assertEqual(summary["failure_family_breakdown"], {"artifact_contract_failure": 1})
            self.assertEqual(
                summary["calibration_matrix"]["failure_family"]["artifact_contract_failure"],
                {
                    "total": 1,
                    "pass_levels": {"L0_FAIL": 1},
                    "l3_pass_rate": 0.0,
                    "l0_contract_failures": 1,
                    "cross_file_consistency_error_rate": 1.0,
                },
            )
            self.assertEqual(labels["pass_level"], "L0_FAIL")
            self.assertFalse(labels["checks"]["l0_complete"])
            self.assertEqual(labels["failure_count"], 1)
            self.assertEqual(diagnosis["stage"], "l0_consistency")

    def test_run_batch_groups_unknown_lint_failures_as_rtl_compile_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_dir = root / "datasets/sample_lint_unknown"
            (sample_dir / "eval").mkdir(parents=True)
            (sample_dir / "attempts/attempt_000").mkdir(parents=True)
            (sample_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "source": "deepseek",
                        "failure_origin": "natural_llm",
                        "requirement_style": "natural_component",
                        "difficulty_tier": "T2",
                        "topology_id": "t2_stream_accumulator",
                        "measurement_point": "b_tool_in_loop_repair",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sample_dir / "eval/labels.json").write_text(
                json.dumps(
                    {
                        "pass_level": "L1",
                        "checks": {
                            "l0_complete": True,
                            "l1_lint_pass": False,
                            "l2_sim_pass": False,
                            "l3_synth_pass": False,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sample_dir / "attempts/attempt_000/diagnosis.json").write_text(
                json.dumps(
                    {
                        "stage": "lint",
                        "failure_type": "unknown",
                        "root_cause": "%Warning-WIDTHEXPAND",
                    }
                )
                + "\n",
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
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, "sample_lint_unknown", 1, "repair_trajectory", sample_dir)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["failure_types"], {"unknown": 1})
            self.assertEqual(summary["failure_family_breakdown"], {"rtl_compile_failure": 1})
            self.assertEqual(
                summary["calibration_matrix"]["failure_family"]["rtl_compile_failure"]["pass_levels"],
                {"L1": 1},
            )

    def test_run_batch_summary_counts_attempt_stage_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_dir = root / "datasets/sample_stage_progress"
            (sample_dir / "eval").mkdir(parents=True)
            (sample_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "source": "deepseek-his-v12",
                        "failure_origin": "natural_llm",
                        "requirement_style": "simple_prompt",
                        "difficulty_tier": "T4",
                        "topology_id": "t4_dual_stream_join",
                        "measurement_point": "b_tool_in_loop_repair",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sample_dir / "eval/labels.json").write_text(
                json.dumps(
                    {
                        "pass_level": "L1",
                        "checks": {
                            "l0_complete": True,
                            "l1_lint_pass": True,
                            "l2_sim_pass": False,
                            "l3_synth_pass": False,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            for attempt_id, stage, failure_type in [
                (0, "l0_consistency", "l0_contract_violation"),
                (1, "lint", "lint_warning_as_error"),
                (2, "sim_run", "functional_mismatch"),
            ]:
                attempt_dir = sample_dir / f"attempts/attempt_{attempt_id:03d}"
                attempt_dir.mkdir(parents=True)
                (attempt_dir / "diagnosis.json").write_text(
                    json.dumps(
                        {
                            "stage": stage,
                            "failure_type": failure_type,
                            "root_cause": "unit test fixture",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=3,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, "sample_stage_progress", 1, "repair_trajectory", sample_dir)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(
                summary["attempt_stage_transition_breakdown"],
                {
                    "l0_consistency->lint": 1,
                    "lint->sim_run": 1,
                },
            )

    def test_run_batch_summary_counts_l4_open_without_treating_not_run_as_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for sample_id, status, skip_reason in [
                ("sample_l4_pass", "pass", None),
                ("sample_l4_fail", "fail", None),
                ("sample_l4_disabled", "not_run", "disabled_by_config"),
                ("sample_l4_l3_failed", "not_run", "l3_failed"),
            ]:
                eval_dir = root / "datasets" / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3",
                            "l4_open_status": status,
                            "l4_open_skip_reason": skip_reason,
                            "checks": {"l0_complete": True, "l3_synth_pass": True},
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            legacy_eval_dir = root / "datasets" / "sample_l4_legacy_false" / "eval"
            legacy_eval_dir.mkdir(parents=True)
            (legacy_eval_dir / "labels.json").write_text(
                json.dumps(
                    {
                        "pass_level": "L3",
                        "checks": {
                            "l0_complete": True,
                            "l3_synth_pass": True,
                            "l4_lite_timing_pass": False,
                        },
                    }
                )
                + "\n",
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
                line_b_targets={"max_samples": 5},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            for sample_id in ("sample_l4_pass", "sample_l4_fail", "sample_l4_disabled", "sample_l4_l3_failed"):
                state = _record_completed_for_test(state, sample_id, 1, "success_l3", root / "datasets" / sample_id)
            state = _record_completed_for_test(
                state,
                "sample_l4_legacy_false",
                1,
                "success_l3",
                root / "datasets" / "sample_l4_legacy_false",
            )

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["l4_open"], {"pass": 1, "fail": 1, "not_run": 3})
            self.assertEqual(
                summary["l4_open_skip_reasons"],
                {"disabled_by_config": 1, "l3_failed": 1, "not_selected_by_policy": 1},
            )

    def test_run_batch_summary_counts_l4_commercial_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [
                ("sample_vivado_pass", "pass", None),
                ("sample_vivado_fail", "fail", None),
                ("sample_vivado_disabled", "not_run", "disabled_by_config"),
                ("sample_vivado_l3_failed", "not_run", "l3_failed"),
            ]
            for sample_id, status, skip_reason in cases:
                eval_dir = root / "datasets" / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3",
                            "l4_open_status": "not_run",
                            "l4_open_skip_reason": "disabled_by_config",
                            "l4_commercial_status": status,
                            "l4_commercial_skip_reason": skip_reason,
                            "checks": {"l0_complete": True, "l3_synth_pass": True},
                        }
                    )
                    + "\n",
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
                line_b_targets={"max_samples": 4},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            for sample_id, _, _ in cases:
                state = _record_completed_for_test(state, sample_id, 1, "success_l3", root / "datasets" / sample_id)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["l4_commercial"], {"pass": 1, "fail": 1, "not_run": 2})
            self.assertEqual(
                summary["l4_commercial_skip_reasons"],
                {"disabled_by_config": 1, "l3_failed": 1},
            )

    def test_run_batch_summary_counts_h_stage_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [
                ("sample_h_pass", "pass", "pass", "pass", "pass"),
                ("sample_h3_na", "pass", "pass", "pass", "not_applicable"),
                ("sample_h3_fail", "pass", "pass", "pass", "fail"),
                ("sample_h1_fail", "pass", "fail", "not_run", "not_run"),
            ]
            for sample_id, h0_status, h1_status, h2_status, h3_status in cases:
                eval_dir = root / "datasets" / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                h3 = h3_status in {"pass", "not_applicable"}
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3" if h3 else "H3_FAIL",
                            "h0_status": h0_status,
                            "h1_status": h1_status,
                            "h2_status": h2_status,
                            "h0_pass": h0_status == "pass",
                            "h1_pass": h1_status == "pass",
                            "h2_pass": h2_status == "pass",
                            "h3_pass": h3,
                            "h3_status": h3_status,
                            "checks": {"l0_complete": h3, "l3_synth_pass": h3},
                        }
                    )
                    + "\n",
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
                line_b_targets={"max_samples": 4},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            for sample_id, *_ in cases:
                state = _record_completed_for_test(state, sample_id, 1, "success_l3", root / "datasets" / sample_id)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["h_stage"]["h0"], {"pass": 4, "fail": 0})
            self.assertEqual(summary["h_stage"]["h1"], {"pass": 3, "fail": 1})
            self.assertEqual(summary["h_stage"]["h2"], {"pass": 3, "fail": 0})
            self.assertEqual(summary["h_stage"]["h3"], {"pass": 1, "fail": 1, "not_applicable": 1})

    def test_run_batch_summary_excludes_oracle_fallback_from_generated_his_pass_credit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [
                ("sample_generated", True, "L3", None),
                ("sample_oracle_fallback", False, "NO_CREDIT_ORACLE_FALLBACK", "oracle_fallback"),
            ]
            for sample_id, generated_credit, generated_level, no_credit_reason in cases:
                eval_dir = root / "datasets" / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3",
                            "highest_official_level": "L3",
                            "generated_his_pass_credit": generated_credit,
                            "generated_his_pass_level": generated_level,
                            "generated_his_no_credit_reason": no_credit_reason,
                            "checks": {"l0_complete": True, "l3_synth_pass": True},
                        }
                    )
                    + "\n",
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
                line_b_targets={"max_samples": 2},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            for sample_id, *_ in cases:
                state = _record_completed_for_test(state, sample_id, 1, "success_l3", root / "datasets" / sample_id)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["pass_level_breakdown"], {"L3": 2})
            self.assertEqual(summary["generated_his_credit"], {"credited": 1, "no_credit_oracle_fallback": 1})
            self.assertEqual(summary["generated_his_pass_level_breakdown"], {"L3": 1})

    def test_run_batch_summary_feeds_derived_training_views_report_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_id = "sample_req2file"
            sample_dir = root / "datasets" / sample_id
            eval_dir = sample_dir / "eval"
            project_dir = sample_dir / "final" / "generated_project"
            eval_dir.mkdir(parents=True)
            project_dir.mkdir(parents=True)
            (project_dir / "manifest.json").write_text("{}\n", encoding="utf-8")
            (project_dir / "rtl_top.v").write_text("module top; endmodule\n", encoding="utf-8")
            (eval_dir / "labels.json").write_text(
                json.dumps({"pass_level": "L3", "checks": {"l0_complete": True, "l3_synth_pass": True}}) + "\n",
                encoding="utf-8",
            )
            (eval_dir / "trajectory.json").write_text(
                json.dumps(
                    {
                        "derived_training_views": {
                            "req2file": {
                                "available": True,
                                "official_eval_unit": True,
                                "standalone_pass_credit": True,
                                "project_level_pass_credit": True,
                            }
                        }
                    }
                )
                + "\n",
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
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, sample_id, 1, "success_l3", sample_dir)

            summary = run_batch_summary_for_test(config, state)
            markdown = render_markdown("run_unit", baseline_rows(summary), summary=summary)

            self.assertEqual(
                summary["derived_training_views"]["req2file"],
                {
                    "available": True,
                    "official_eval_unit": False,
                    "standalone_pass_credit": False,
                    "project_level_pass_credit": False,
                    "rows": 2,
                    "file_level_passed": 0,
                },
            )
            self.assertIn("## Derived Training Views", markdown)
            self.assertIn("| req2file | yes | no | no | 2 | 0 |", markdown)

    def test_run_batch_summary_ignores_malformed_derived_training_trajectory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_id = "sample_malformed_trajectory"
            sample_dir = root / "datasets" / sample_id
            eval_dir = sample_dir / "eval"
            project_dir = sample_dir / "final" / "generated_project"
            eval_dir.mkdir(parents=True)
            project_dir.mkdir(parents=True)
            (project_dir / "manifest.json").write_text("{}\n", encoding="utf-8")
            (eval_dir / "labels.json").write_text(
                json.dumps({"pass_level": "L3", "checks": {"l3_synth_pass": True}}) + "\n",
                encoding="utf-8",
            )
            (eval_dir / "trajectory.json").write_text("[]\n", encoding="utf-8")
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, sample_id, 1, "success_l3", sample_dir)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["derived_training_views"], {})

    def test_run_batch_summary_ignores_non_utf8_derived_training_trajectory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_id = "sample_non_utf8_trajectory"
            sample_dir = root / "datasets" / sample_id
            eval_dir = sample_dir / "eval"
            project_dir = sample_dir / "final" / "generated_project"
            eval_dir.mkdir(parents=True)
            project_dir.mkdir(parents=True)
            (project_dir / "manifest.json").write_text("{}\n", encoding="utf-8")
            (eval_dir / "labels.json").write_text(
                json.dumps({"pass_level": "L3", "checks": {"l3_synth_pass": True}}) + "\n",
                encoding="utf-8",
            )
            (eval_dir / "trajectory.json").write_bytes(b"\xff\xfe\x00")
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, sample_id, 1, "success_l3", sample_dir)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["derived_training_views"], {})

    def test_run_batch_summary_sanitizes_malformed_req2file_view_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_id = "sample_malformed_req2file_fields"
            sample_dir = root / "datasets" / sample_id
            eval_dir = sample_dir / "eval"
            project_dir = sample_dir / "final" / "generated_project"
            eval_dir.mkdir(parents=True)
            project_dir.mkdir(parents=True)
            (project_dir / "manifest.json").write_text("{}\n", encoding="utf-8")
            (project_dir / "rtl_top.v").write_text("module top; endmodule\n", encoding="utf-8")
            (eval_dir / "labels.json").write_text(
                json.dumps({"pass_level": "L3", "checks": {"l3_synth_pass": True}}) + "\n",
                encoding="utf-8",
            )
            (eval_dir / "trajectory.json").write_text(
                json.dumps(
                    {
                        "derived_training_views": {
                            "req2file": {
                                "available": True,
                                "official_eval_unit": True,
                                "standalone_pass_credit": True,
                                "project_level_pass_credit": True,
                                "rows": "not-an-int",
                                "file_level_passed": "also-not-an-int",
                            }
                        }
                    }
                )
                + "\n",
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
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, sample_id, 1, "success_l3", sample_dir)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(
                summary["derived_training_views"]["req2file"],
                {
                    "available": True,
                    "official_eval_unit": False,
                    "standalone_pass_credit": False,
                    "project_level_pass_credit": False,
                    "rows": 2,
                    "file_level_passed": 0,
                },
            )

    def test_run_batch_summary_counts_l4_as_l3_surviving_pass_rate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_id = "sample_l4_pass"
            eval_dir = root / "datasets" / sample_id / "eval"
            eval_dir.mkdir(parents=True)
            (eval_dir / "labels.json").write_text(
                json.dumps(
                    {
                        "pass_level": "L4",
                        "checks": {"l0_complete": True, "l3_synth_pass": True, "l4_open_pass": True},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "datasets" / sample_id / "metadata.json").write_text(
                json.dumps({"difficulty_tier": "T3"}) + "\n",
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
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, sample_id, 1, "success_l3", root / "datasets" / sample_id)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["pass_level_breakdown"], {"L4": 1})
            self.assertEqual(summary["calibration_matrix"]["difficulty_tier"]["T3"]["l3_pass_rate"], 1.0)

    def test_run_batch_summary_reports_l0_l4_survival_levels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [
                (
                    "sample_l3",
                    {
                        "l0_complete": True,
                        "l1_lint_pass": True,
                        "l2_sim_pass": True,
                        "l3_synth_pass": True,
                    },
                    "not_run",
                ),
                (
                    "sample_l1",
                    {
                        "l0_complete": True,
                        "l1_lint_pass": True,
                        "l2_sim_pass": False,
                        "l3_synth_pass": False,
                    },
                    "not_run",
                ),
                (
                    "sample_l4",
                    {
                        "l0_complete": True,
                        "l1_lint_pass": True,
                        "l2_sim_pass": True,
                        "l3_synth_pass": True,
                    },
                    "pass",
                ),
            ]
            for sample_id, checks, l4_status in cases:
                eval_dir = root / "datasets" / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L4" if l4_status == "pass" else ("L3" if checks["l3_synth_pass"] else "L1"),
                            "checks": checks,
                            "l4_open_status": l4_status,
                        }
                    )
                    + "\n",
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
                line_b_targets={"max_samples": 3},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            for sample_id, *_ in cases:
                state = _record_completed_for_test(state, sample_id, 1, "success_l3", root / "datasets" / sample_id)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["levels"]["l0"], {"pass": 3, "fail": 0})
            self.assertEqual(summary["levels"]["l1"], {"pass": 3, "fail": 0})
            self.assertEqual(summary["levels"]["l2"], {"pass": 2, "fail": 1})
            self.assertEqual(summary["levels"]["l3"], {"pass": 2, "fail": 1})
            self.assertEqual(summary["levels"]["l4_open"], {"pass": 1, "fail": 0, "not_run": 2})

    def test_run_batch_summary_computes_patch_regression_rate_from_valid_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patches_by_sample = {
                "sample_fixed": [
                    {
                        "status": "valid",
                        "automatic_pass_credit": True,
                        "regressions": [],
                        "repair_regression": {"fixed_target": True, "regressed_levels": []},
                    }
                ],
                "sample_regressed": [
                    {
                        "status": "valid",
                        "automatic_pass_credit": False,
                        "regressions": ["lint"],
                        "repair_regression": {"fixed_target": False, "regressed_levels": ["lint"]},
                    }
                ],
                "sample_invalid": [
                    {
                        "status": "invalid_edit_surface",
                        "automatic_pass_credit": False,
                        "regressions": [],
                        "repair_regression": {"fixed_target": False, "regressed_levels": []},
                    }
                ],
            }
            for sample_id, patches in patches_by_sample.items():
                eval_dir = root / "datasets" / sample_id / "eval"
                eval_dir.mkdir(parents=True)
                (eval_dir / "labels.json").write_text(
                    json.dumps({"pass_level": "L2", "checks": {"l0_complete": True}}) + "\n",
                    encoding="utf-8",
                )
                (eval_dir / "trajectory.json").write_text(
                    json.dumps({"patches": patches}) + "\n",
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
                line_b_targets={"max_samples": 3},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            for sample_id in patches_by_sample:
                state = _record_completed_for_test(
                    state,
                    sample_id,
                    1,
                    "repair_trajectory",
                    root / "datasets" / sample_id,
                )

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(
                summary["repair_metrics"],
                {
                    "total_patches": 3,
                    "valid_patches": 2,
                    "invalid_edit_surface": 1,
                    "fixed_target": 1,
                    "automatic_pass_credit": 1,
                    "regressing_patches": 1,
                    "regression_rate": 0.5,
                },
            )

    def test_run_batch_summary_counts_toolchain_environment_failures_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eval_dir = root / "datasets" / "sample_l4_env_failure" / "eval"
            eval_dir.mkdir(parents=True)
            (eval_dir / "labels.json").write_text(
                json.dumps(
                    {
                        "pass_level": "L3",
                        "l4_open_status": "not_run",
                        "l4_open_skip_reason": "toolchain_environment_failure",
                        "checks": {"l0_complete": True, "l3_synth_pass": True},
                    }
                )
                + "\n",
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
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, "sample_l4_env_failure", 1, "success_l3", root / "datasets" / "sample_l4_env_failure")

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["l4_open"], {"pass": 0, "fail": 0, "not_run": 1})
            self.assertEqual(summary["toolchain_environment_failures"], {"l4_open": 1})

    def test_run_batch_summary_counts_independent_oracle_without_infrastructure_in_model_denominator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = {
                "sample_pass": ("pass", "fir_filter", "numeric", None),
                "sample_fail": ("fail", "fir_filter", "numeric", "natural_model_failure"),
                "sample_not_run": ("not_run", "counter", "control", None),
                "sample_infra": (
                    "infrastructure_error",
                    "matrix_vector_mac",
                    "numeric",
                    "oracle_environment_failure",
                ),
            }
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            for index, (sample_id, (status, family_id, domain, failure_origin)) in enumerate(cases.items(), 1):
                sample_dir = root / "datasets" / sample_id
                eval_dir = sample_dir / "eval"
                eval_dir.mkdir(parents=True)
                (sample_dir / "metadata.json").write_text(
                    json.dumps({"family_id": family_id, "oracle_domain": domain}) + "\n",
                    encoding="utf-8",
                )
                (eval_dir / "labels.json").write_text(
                    json.dumps(
                        {
                            "pass_level": "L3" if status in {"pass", "not_run"} else "L1",
                            "independent_oracle_status": status,
                            "failure_origin": failure_origin,
                            "checks": {"l0_complete": True},
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                state = _record_completed_for_test(state, sample_id, index, "success_l3", sample_dir)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 4},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )

            summary = run_batch_summary_for_test(config, state)["independent_oracle"]

            self.assertEqual(
                {key: summary[key] for key in ("pass", "fail", "not_run", "infrastructure_error")},
                {"pass": 1, "fail": 1, "not_run": 1, "infrastructure_error": 1},
            )
            self.assertEqual(summary["model_denominator"], 2)
            self.assertEqual(summary["model_failures"], 1)
            self.assertEqual(summary["by_domain"]["numeric"]["infrastructure_error"], 1)
            self.assertEqual(summary["by_family"]["fir_filter"]["pass"], 1)

    def test_run_batch_summary_counts_latent_testbench_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_dir = root / "datasets/sample_latent_testbench_race"
            attempt_project = sample_dir / "attempts/attempt_000/generated_project"
            (sample_dir / "eval").mkdir(parents=True)
            (attempt_project / "sim").mkdir(parents=True)
            (sample_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "source": "deepseek-his-v12",
                        "failure_origin": "natural_llm",
                        "requirement_style": "simple_prompt",
                        "difficulty_tier": "T4",
                        "topology_id": "t4_dual_stream_join",
                        "measurement_point": "b_tool_in_loop_repair",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sample_dir / "eval/labels.json").write_text(
                json.dumps(
                    {
                        "pass_level": "L0_FAIL",
                        "checks": {
                            "l0_complete": False,
                            "l1_lint_pass": False,
                            "l2_sim_pass": False,
                            "l3_synth_pass": False,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sample_dir / "attempts/attempt_000/diagnosis.json").write_text(
                json.dumps(
                    {
                        "stage": "l0_consistency",
                        "failure_type": "l0_contract_violation",
                        "root_cause": "unit test fixture",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (attempt_project / "sim/tb_top.v").write_text(
                """
module tb;
  initial begin
    wait(out_valid);
    @(posedge clk) #1;
    if (out_data !== expected) $display("TEST_FAIL");
  end
endmodule
""",
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
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(
                state,
                "sample_latent_testbench_race",
                1,
                "repair_trajectory",
                sample_dir,
            )

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["failure_family_breakdown"], {"artifact_contract_failure": 1})
            self.assertEqual(
                summary["latent_testbench_issue_breakdown"],
                {"testbench_observation_race": 1},
            )

    def test_run_batch_groups_rtl_identifier_check_as_compile_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample_dir = root / "datasets/sample_rtl_identifier"
            (sample_dir / "eval").mkdir(parents=True)
            (sample_dir / "attempts/attempt_000").mkdir(parents=True)
            (sample_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "source": "deepseek-his-v12",
                        "failure_origin": "natural_llm",
                        "requirement_style": "simple_prompt",
                        "difficulty_tier": "T4",
                        "topology_id": "t4_dual_stream_join",
                        "measurement_point": "a_first_attempt_no_tools",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sample_dir / "eval/labels.json").write_text(
                json.dumps(
                    {
                        "pass_level": "L0",
                        "checks": {
                            "l0_complete": True,
                            "l1_lint_pass": False,
                            "l2_sim_pass": False,
                            "l3_synth_pass": False,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (sample_dir / "attempts/attempt_000/diagnosis.json").write_text(
                json.dumps(
                    {
                        "stage": "rtl_identifier_check",
                        "failure_type": "rtl_reserved_identifier",
                        "root_cause": "rtl/top.v:12: Verilog reserved keyword 'buf' used as declared signal",
                    }
                )
                + "\n",
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
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )
            state = initial_run_state("run_unit", config_fingerprint="f" * 64)
            state = _record_completed_for_test(state, "sample_rtl_identifier", 1, "repair_trajectory", sample_dir)

            summary = run_batch_summary_for_test(config, state)

            self.assertEqual(summary["failure_types"], {"rtl_reserved_identifier": 1})
            self.assertEqual(summary["failure_family_breakdown"], {"rtl_compile_failure": 1})

    def test_runner_main_loads_config_and_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": str(root / "datasets"),
                        "export_root": str(root / "exports"),
                        "run_root": str(root / "runs"),
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": True,
                        "line_b_targets": {"max_samples": 1},
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4],
                                "count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            output = run_main_for_test(["--config", str(config_path), "--run-id", "run_cli_unit"])

            self.assertIn("run_id=run_cli_unit", output)
            self.assertIn("total_completed=1", output)

    def test_runner_main_preflight_prints_json_without_running_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": str(root / "datasets"),
                        "export_root": str(root / "exports"),
                        "run_root": str(root / "runs"),
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": False,
                        "line_b_targets": {"max_samples": 1},
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4],
                                "count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch("LLM.src.sr2fpga_agent.runner.shutil.which", return_value="/usr/bin/tool"):
                output = run_main_for_test(["--config", str(config_path), "--run-id", "preflight_unit", "--preflight"])

            report = json.loads(output)
            self.assertTrue(report["ok"])
            self.assertEqual(report["planned_samples"], 1)
            self.assertFalse((root / "datasets").exists())


def run_main_for_test(argv: list[str]) -> str:
    import io
    from contextlib import redirect_stdout

    from LLM.src.sr2fpga_agent import runner

    output = io.StringIO()
    with redirect_stdout(output):
        runner.main(argv)
    return output.getvalue()
