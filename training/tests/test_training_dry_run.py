import json
import io
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

from sr2fpga_training.training_dry_run import (
    DryRunError,
    dry_run_chat_jsonl,
    dry_run_from_config,
    main,
)


class TrainingDryRunTest(unittest.TestCase):
    def test_reports_length_stats_and_truncation_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            train_file = Path(tmp) / "train.jsonl"
            train_file.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "messages": [
                                    {"role": "user", "content": "short prompt"},
                                    {"role": "assistant", "content": "short answer"},
                                ]
                            }
                        ),
                        json.dumps(
                            {
                                "messages": [
                                    {"role": "user", "content": " ".join(["token"] * 20)},
                                    {"role": "assistant", "content": " ".join(["answer"] * 20)},
                                ]
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = dry_run_chat_jsonl(train_file, max_seq_length=16)

            self.assertEqual(report["rows"], 2)
            self.assertEqual(report["valid_rows"], 2)
            self.assertEqual(report["over_max_seq_length"], 1)
            self.assertFalse(report["fits_max_seq_length"])
            self.assertGreaterEqual(report["max_tokens"], report["min_tokens"])
            self.assertEqual(report["max_seq_length"], 16)

    def test_dry_run_from_config_uses_train_file_and_max_seq_length(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train_file = root / "train.jsonl"
            config_path = root / "train.yaml"
            train_file.write_text(
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "Generate RTL."},
                            {"role": "assistant", "content": "module top; endmodule"},
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            config_path.write_text(
                "\n".join(
                    [
                        f"train_file: {train_file}",
                        "max_seq_length: 8",
                        "model_name_or_path: /tmp/no-model-needed",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = dry_run_from_config(config_path)

            self.assertEqual(report["train_file"], str(train_file))
            self.assertEqual(report["max_seq_length"], 8)
            self.assertEqual(report["rows"], 1)

    def test_cli_can_fail_on_truncation_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            train_file = Path(tmp) / "train.jsonl"
            train_file.write_text(
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": " ".join(["token"] * 20)},
                            {"role": "assistant", "content": "answer"},
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("sys.stdout", new=io.StringIO()), patch(
                "sys.argv",
                [
                    "training_dry_run",
                    "--input",
                    str(train_file),
                    "--max-seq-length",
                    "8",
                    "--fail-on-truncation",
                ],
            ):
                with self.assertRaises(SystemExit) as raised:
                    main()

            self.assertEqual(raised.exception.code, 1)

    def test_rejects_chat_rows_without_assistant_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            train_file = Path(tmp) / "train.jsonl"
            train_file.write_text(
                json.dumps({"messages": [{"role": "user", "content": "Generate RTL."}]}) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(DryRunError, "assistant"):
                dry_run_chat_jsonl(train_file, max_seq_length=16)


if __name__ == "__main__":
    unittest.main()
