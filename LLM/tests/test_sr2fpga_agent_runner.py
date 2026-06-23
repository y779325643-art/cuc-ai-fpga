import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.runner import (
    RunnerConfig,
    TaskConfig,
    load_runner_config,
    planned_samples,
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
            self.assertEqual(config.line_b_targets["l3_success_ratio"], 0.4)
            self.assertEqual(config.line_b_targets["repair_trajectory_ratio"], 0.6)
            self.assertEqual(config.line_b_targets["max_samples"], 3)
            self.assertEqual(config.tasks[0].source, "deterministic")
            self.assertEqual(config.tasks[0].task_type, "counter")
            self.assertEqual(config.tasks[0].widths, [4, 8])
            self.assertEqual(config.tasks[0].count, 2)

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
