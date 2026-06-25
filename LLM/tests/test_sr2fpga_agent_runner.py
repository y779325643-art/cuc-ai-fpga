import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from LLM.src.sr2fpga_agent.runner import (
    RunState,
    RunnerConfig,
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
    _record_completed as _record_completed_for_test,
    _summary as run_batch_summary_for_test,
)


class RunnerConfigTest(unittest.TestCase):
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
            self.assertEqual(config.tasks[0].difficulty_tier, "T1")
            self.assertEqual(config.tasks[0].failure_origin, "")
            self.assertEqual(config.tasks[0].topology_ids, [])
            self.assertEqual(config.tasks[0].measurement_point, "")
            self.assertEqual(config.tasks[0].requirement_style, "contract")

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
                                "difficulty_tier": "T2",
                                "failure_origin": "synthetic_injected",
                                "measurement_point": "b_tool_in_loop_repair",
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
            self.assertEqual(config.tasks[0].difficulty_tier, "T2")
            self.assertEqual(config.tasks[0].failure_origin, "synthetic_injected")
            self.assertEqual(config.tasks[0].measurement_point, "b_tool_in_loop_repair")
            self.assertEqual(config.tasks[0].requirement_style, "natural_component")

    def test_baseline_b_example_config_is_tool_loop_repair_measurement(self) -> None:
        config = load_runner_config(Path("configs/sr2fpga_baseline_b.example.yaml"))
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

    def test_baseline_b_smoke_config_uses_tightened_prompt_namespace(self) -> None:
        config = load_runner_config(Path("configs/sr2fpga_baseline_b_smoke.example.yaml"))
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
        config = load_runner_config(Path("configs/sr2fpga_baseline_b_tightened.example.yaml"))
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
        config = load_runner_config(Path("configs/sr2fpga_baseline_b_t3_t4_smoke.example.yaml"))
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

    def test_his_v12_smoke_config_targets_t4_two_stage_provider(self) -> None:
        config = load_runner_config(Path("configs/sr2fpga_his_v12_smoke.example.yaml"))
        samples = planned_samples(config)

        self.assertEqual(config.provider, "deepseek-his-v12")
        self.assertEqual(config.repair_provider, "none")
        self.assertEqual(config.max_attempts, 1)
        self.assertEqual(config.sample_id_prefix, "his_v12_smoke_v6")
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].source, "deepseek-his-v12")
        self.assertEqual(samples[0].topology_id, "t4_dual_stream_join")
        self.assertEqual(samples[0].sample_id, "sample_his_v12_smoke_v6_t4_dual_stream_join_8_000001")
        self.assertEqual(samples[0].requirement_style, "simple_prompt")
        self.assertEqual(
            samples[0].requirement,
            "Generate an 8-bit FPGA RTL project that joins two input streams, accumulates joined samples, and exposes one output stream.",
        )
        self.assertEqual(samples[0].metadata(config)["measurement_point"], "a_first_attempt_no_tools")
        self.assertEqual(samples[0].metadata(config)["system_his_schema_version"], "system-his-v1.2")
        self.assertEqual(samples[0].metadata(config)["training_split"], "clean")

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

    def test_load_baseline_a_example_config_targets_first_attempt_no_tools(self) -> None:
        config_path = Path(__file__).resolve().parents[2] / "configs" / "sr2fpga_baseline_a.example.yaml"

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
                ("deepseek", "composed_stream_fork", "t3_stream_fork", "T3"),
                ("deepseek", "composed_dual_stream_join", "t4_dual_stream_join", "T4"),
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
                        "width": 4,
                        "requirement_style": "contract",
                        "requirement": (
                            "Design a 4-bit counter as a complete SR2FPGA Verilog RTL project. "
                            "Use multi-file RTL for FIFO, SPI, UART, PWM, and controller-style tasks; "
                            "include system_his.json, manifest.json, timing constraints, a bounded "
                            "self-checking testbench that prints TEST_PASS on success or TEST_FAIL on "
                            "failure, and predicted QoR."
                        ),
                        "difficulty_tier": "T1",
                        "topology_id": "",
                        "failure_origin": "natural_llm",
                        "measurement_point": "a_first_attempt_no_tools",
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
                patch("LLM.src.sr2fpga_agent.runner.DeepSeekClient") as client_cls,
            ):
                client_cls.return_value.chat.return_value = '{"ok": true}'
                report = runner_preflight(config, run_id="auth_ok", validate_provider=True)

            self.assertTrue(report["ok"])
            self.assertEqual(report["provider_auth"]["deepseek"]["status"], "ok")
            self.assertNotIn("shell-fake-key", json.dumps(report))

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
                patch("LLM.src.sr2fpga_agent.runner.DeepSeekClient") as client_cls,
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

    def test_baseline_a_preflight_sample_preview_lists_t1_to_t4_topologies(self) -> None:
        config_path = Path(__file__).resolve().parents[2] / "configs" / "sr2fpga_baseline_a.example.yaml"
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
                ("composed_stream_fork", "t3_stream_fork", "T3"),
                ("composed_dual_stream_join", "t4_dual_stream_join", "T4"),
            ],
        )
        t4_requirement = report["samples"][3]["requirement"]
        self.assertEqual(report["samples"][3]["requirement_style"], "natural_component")
        self.assertIn("Build an 8-bit dual-stream join datapath", t4_requirement)
        self.assertIn("t4_dual_stream_join", t4_requirement)
        self.assertIn("difficulty tier T4", t4_requirement)
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
                TaskConfig(source="deepseek", task_type="counter", widths=[4], count=1, difficulty_tier="T2"),
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
        self.assertEqual(samples[0].metadata(config)["difficulty_tier"], "T2")
        self.assertEqual(samples[0].metadata(config)["measurement_point"], "b_tool_in_loop_repair")
        self.assertEqual(samples[1].metadata(config)["failure_origin"], "synthetic_injected")

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
                    difficulty_tier="T2",
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
            line_b_targets={"max_samples": 4},
            tasks=[
                TaskConfig(
                    source="deterministic",
                    task_type="component_topology",
                    widths=[8],
                    count=4,
                    topology_ids=[
                        "t1_event_counter",
                        "t2_stream_accumulator",
                        "t3_stream_fork",
                        "t4_dual_stream_join",
                    ],
                    failure_origin="compositional_assembly",
                )
            ],
        )

        samples = planned_samples(config)

        self.assertEqual(
            [(item.sample_id, item.task_type, item.topology_id, item.difficulty_tier) for item in samples],
            [
                ("sample_runner_t1_event_counter_8_000001", "composed_event_counter", "t1_event_counter", "T1"),
                (
                    "sample_runner_t2_stream_accumulator_8_000002",
                    "composed_stream_accumulator",
                    "t2_stream_accumulator",
                    "T2",
                ),
                ("sample_runner_t3_stream_fork_8_000003", "composed_stream_fork", "t3_stream_fork", "T3"),
                (
                    "sample_runner_t4_dual_stream_join_8_000004",
                    "composed_dual_stream_join",
                    "t4_dual_stream_join",
                    "T4",
                ),
            ],
        )
        self.assertEqual(samples[0].metadata(config)["topology_id"], "t1_event_counter")
        self.assertEqual(samples[1].metadata(config)["topology_id"], "t2_stream_accumulator")
        self.assertEqual(samples[2].metadata(config)["topology_id"], "t3_stream_fork")
        self.assertEqual(samples[3].metadata(config)["topology_id"], "t4_dual_stream_join")
        self.assertEqual(samples[3].metadata(config)["requirement_style"], "contract")
        self.assertIn("component topology t1_event_counter", samples[0].requirement)
        self.assertIn("event_gate", samples[0].requirement)
        self.assertIn("counter_core", samples[0].requirement)
        self.assertIn("event_valid pulses", samples[0].requirement)
        self.assertIn("component topology t4_dual_stream_join", samples[3].requirement)
        self.assertIn("skid_a:skid_buffer", samples[3].requirement)
        self.assertIn("skid_b:skid_buffer", samples[3].requirement)
        self.assertIn("stream_join.out_data -> accumulator_core.sample", samples[3].requirement)
        self.assertIn("Keep rtl/top.v as the integration wrapper", samples[3].requirement)

    def test_classify_sample_bucket(self) -> None:
        self.assertEqual(classify_sample_bucket({"pass_level": "L3", "failure_count": 0}), "success_l3")
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
            self.assertEqual(summary["metadata_breakdown"]["difficulty_tier"]["T1"], 1)
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
                        "difficulty_tier": "T1",
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
            self.assertIn("| difficulty_tier | T1 | 1 | L3:1 | 100.0% | 0 | 0.0% |", baseline_report)
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((root / "datasets/sample_runner_counter_4_000001/eval/labels.json").exists())
            metadata = json.loads(
                (root / "datasets/sample_runner_counter_4_000001/metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["failure_origin"], "deterministic_template")
            self.assertEqual(metadata["measurement_point"], "a_first_attempt_no_tools")
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
