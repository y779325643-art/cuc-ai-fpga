import json
import tempfile
import unittest
from pathlib import Path

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
    should_skip_sample,
    write_run_state,
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

    def test_classify_sample_bucket(self) -> None:
        self.assertEqual(classify_sample_bucket({"pass_level": "L3", "failure_count": 0}), "success_l3")
        self.assertEqual(classify_sample_bucket({"pass_level": "L1", "failure_count": 2}), "repair_trajectory")
        self.assertEqual(classify_sample_bucket({"pass_level": "L0", "failure_count": 0}), "rejected")

    def test_initial_run_state_defaults(self) -> None:
        state = initial_run_state("run_test")

        self.assertEqual(state.run_id, "run_test")
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
            )

            write_run_state(state_path, state)
            self.assertTrue(state_path.read_text(encoding="utf-8").endswith("\n"))
            loaded = read_run_state(state_path)

            self.assertEqual(loaded.run_id, "run_test")
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
            self.assertEqual(summary["total_completed"], 1)
            self.assertEqual(summary["next_index"], 1)
            self.assertEqual(summary["buckets"]["success_l3"], ["sample_runner_counter_4_000001"])
            self.assertEqual(state.next_index, 1)
            self.assertEqual(
                events,
                [
                    {
                        "event": "sample_completed",
                        "sample_id": "sample_runner_counter_4_000001",
                        "task_type": "counter",
                        "width": 4,
                        "pass_level": "L3",
                        "bucket": "success_l3",
                    }
                ],
            )
            self.assertTrue((run_dir / "run_state.json").exists())
            self.assertTrue((run_dir / "summary.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((root / "datasets/sample_runner_counter_4_000001/eval/labels.json").exists())
            self.assertTrue((root / "exports/requirement_to_project.jsonl").exists())

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
