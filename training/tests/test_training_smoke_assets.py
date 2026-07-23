import json
from pathlib import Path
import tempfile
import unittest

import yaml

from sr2fpga_training.prepare_dataset import convert_jsonl
from sr2fpga_training.training_dry_run import dry_run_chat_jsonl


REPO_ROOT = Path(__file__).resolve().parents[2]


class TrainingSmokeAssetsTest(unittest.TestCase):
    def test_smoke_dataset_can_be_converted_to_chat_jsonl(self) -> None:
        source = REPO_ROOT / "LLM/data/examples/smoke_verilog_raw.jsonl"
        target = REPO_ROOT / "tmp/test_smoke_train.jsonl"

        count = convert_jsonl(source, target)
        rows = [
            json.loads(line)
            for line in target.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertGreaterEqual(count, 6)
        self.assertEqual(count, len(rows))
        self.assertTrue(all("messages" in row for row in rows))

    def test_t0_t4_export_views_can_be_converted_to_chat_jsonl(self) -> None:
        export_dir = REPO_ROOT / "datasets/sr2fpga_rtl_v1_exports"
        sample_prefix = "sample_t0_t4_deterministic_smoke_"
        views = [
            "requirement_to_his.jsonl",
            "his_to_project.jsonl",
            "requirement_to_project.jsonl",
            "requirement_to_file.jsonl",
            "project_to_predicted_qor.jsonl",
            "project_to_measured_qor.jsonl",
        ]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for view in views:
                source = export_dir / view
                source_rows = [
                    json.loads(line)
                    for line in source.read_text(encoding="utf-8").splitlines()
                    if line.strip() and json.loads(line).get("sample_id", "").startswith(sample_prefix)
                ]
                filtered = tmp_dir / view
                target = tmp_dir / view.replace(".jsonl", ".chat.jsonl")
                filtered.write_text(
                    "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in source_rows),
                    encoding="utf-8",
                )

                count = convert_jsonl(filtered, target)
                rows = [
                    json.loads(line)
                    for line in target.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

                expected_rows = 24 if view != "requirement_to_file.jsonl" else len(source_rows)
                if view == "requirement_to_file.jsonl":
                    self.assertGreater(expected_rows, 100, view)
                self.assertEqual(len(source_rows), expected_rows, view)
                self.assertEqual(count, expected_rows, view)
                self.assertEqual(len(rows), expected_rows, view)
                self.assertTrue(all("messages" in row for row in rows), view)
                self.assertTrue(
                    all(
                        any(message["role"] == "user" for message in row["messages"])
                        and any(message["role"] == "assistant" for message in row["messages"])
                        for row in rows
                    ),
                    view,
                )
                report = dry_run_chat_jsonl(target, max_seq_length=65536)
                self.assertEqual(report["rows"], expected_rows, view)
                self.assertTrue(report["fits_max_seq_length"], view)

    def test_t0_t4_requirement_to_file_non_his_rows_fit_short_context(self) -> None:
        source = REPO_ROOT / "datasets/sr2fpga_rtl_v1_exports/requirement_to_file.jsonl"
        sample_prefix = "sample_t0_t4_deterministic_smoke_"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            source_rows = [
                json.loads(line)
                for line in source.read_text(encoding="utf-8").splitlines()
                if line.strip()
                and json.loads(line).get("sample_id", "").startswith(sample_prefix)
                and json.loads(line).get("file_path") != "system_his.json"
            ]
            filtered = tmp_dir / "requirement_to_file_short.jsonl"
            target = tmp_dir / "requirement_to_file_short.chat.jsonl"
            filtered.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in source_rows),
                encoding="utf-8",
            )

            count = convert_jsonl(filtered, target)
            report = dry_run_chat_jsonl(target, max_seq_length=2048)

            self.assertEqual(count, len(source_rows))
            self.assertGreater(count, 100)
            self.assertTrue(report["fits_max_seq_length"])
            self.assertEqual(report["over_max_seq_length"], 0)

    def test_qwen_smoke_training_config_uses_local_model_and_small_run(self) -> None:
        config_path = REPO_ROOT / "LLM/configs/train_qwen_smoke.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        self.assertEqual(
            config["model_name_or_path"],
            "/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct",
        )
        self.assertEqual(config["train_file"], "LLM/data/train.jsonl")
        self.assertEqual(config["output_dir"], "/mnt/e/Aowen/runs/qwen2_5_coder_7b_smoke_lora")
        self.assertLessEqual(config["max_seq_length"], 512)
        self.assertLessEqual(config["max_steps"], 20)
        self.assertTrue(config["use_qlora"])

    def test_qwen_req2file_short_training_config_uses_short_context_dataset(self) -> None:
        config_path = REPO_ROOT / "LLM/configs/train_qwen_req2file_short.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        self.assertEqual(
            config["model_name_or_path"],
            "/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct",
        )
        self.assertEqual(config["train_file"], "LLM/data/t0_t4_req2file_short.chat.jsonl")
        self.assertEqual(config["output_dir"], "/mnt/e/Aowen/runs/qwen2_5_coder_7b_req2file_short_lora")
        self.assertEqual(config["max_seq_length"], 2048)
        self.assertLessEqual(config["max_steps"], 50)
        self.assertTrue(config["use_qlora"])


if __name__ == "__main__":
    unittest.main()
