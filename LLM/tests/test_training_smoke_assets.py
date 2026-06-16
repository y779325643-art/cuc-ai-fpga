import json
from pathlib import Path
import unittest

import yaml

from LLM.src.prepare_dataset import convert_jsonl


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


if __name__ == "__main__":
    unittest.main()
