import json
from pathlib import Path
import tempfile
import unittest

from LLM.src.prepare_dataset import DatasetFormatError, convert_jsonl


class PrepareDatasetTest(unittest.TestCase):
    def test_convert_prompt_completion_rows_to_messages_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "raw.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "instruction": "Write Verilog for a 2-input AND gate.",
                        "input": "Use module name and2.",
                        "output": "module and2(input a, input b, output y); assign y = a & b; endmodule",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            row = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(
                row["messages"],
                [
                    {
                        "role": "user",
                        "content": "Write Verilog for a 2-input AND gate.\n\nUse module name and2.",
                    },
                    {
                        "role": "assistant",
                        "content": "module and2(input a, input b, output y); assign y = a & b; endmodule",
                    },
                ],
            )

    def test_accepts_existing_messages_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "raw.jsonl"
            target = Path(tmp) / "train.jsonl"
            messages = [
                {"role": "user", "content": "Explain timing closure."},
                {"role": "assistant", "content": "Timing closure ensures paths meet constraints."},
            ]
            source.write_text(json.dumps({"messages": messages}) + "\n", encoding="utf-8")

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["messages"], messages)

    def test_rejects_rows_missing_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "raw.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(json.dumps({"instruction": "Explain FSM design."}) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(DatasetFormatError, "missing assistant response"):
                convert_jsonl(source, target)

    def test_rejects_invalid_json_with_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "raw.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text('{"instruction": "broken"\n', encoding="utf-8")

            with self.assertRaisesRegex(DatasetFormatError, "line 1"):
                convert_jsonl(source, target)


if __name__ == "__main__":
    unittest.main()
