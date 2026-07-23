import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sr2fpga_training.prepare_dataset import DatasetFormatError, convert_jsonl


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

    def test_converts_requirement_to_his_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirement_to_his.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "requirement": "Design an 8-bit counter.",
                        "system_his": {"schema_version": "system-his-v1.2", "task_type": "counter"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("SR2FPGA requirement", messages[0]["content"])
            self.assertIn("Design an 8-bit counter.", messages[0]["content"])
            self.assertEqual(json.loads(messages[1]["content"])["task_type"], "counter")

    def test_converts_his_to_project_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "his_to_project.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "system_his": {"schema_version": "system-his-v1.2", "task_type": "counter"},
                        "files": [{"path": "rtl/top.v", "content": "module top; endmodule\n"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("System-HIS JSON", messages[0]["content"])
            self.assertIn("system-his-v1.2", messages[0]["content"])
            self.assertEqual(json.loads(messages[1]["content"])[0]["path"], "rtl/top.v")

    def test_converts_requirement_to_project_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirement_to_project.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "requirement": "Design an 8-bit counter.",
                        "files": [{"path": "rtl/top.v", "content": "module top; endmodule\n"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("complete SR2FPGA project files", messages[0]["content"])
            self.assertIn("Design an 8-bit counter.", messages[0]["content"])
            self.assertEqual(json.loads(messages[1]["content"])[0]["content"], "module top; endmodule\n")

    def test_converts_requirement_to_file_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirement_to_file.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "requirement": "Design an 8-bit counter.",
                        "file_path": "rtl/top.v",
                        "file_content": "module top; endmodule\n",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("Generate this SR2FPGA project file", messages[0]["content"])
            self.assertIn("rtl/top.v", messages[0]["content"])
            self.assertIn("Design an 8-bit counter.", messages[0]["content"])
            self.assertEqual(messages[1]["content"], "module top; endmodule")

    def test_filters_rows_by_sample_prefix_and_excluded_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirement_to_file.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        {
                            "sample_id": "sample_t0_t4_demo_000001",
                            "requirement": "Design a counter.",
                            "file_path": "rtl/top.v",
                            "file_content": "module top; endmodule\n",
                        },
                        {
                            "sample_id": "sample_t0_t4_demo_000001",
                            "requirement": "Design a counter.",
                            "file_path": "system_his.json",
                            "file_content": "{}\n",
                        },
                        {
                            "sample_id": "sample_other_000001",
                            "requirement": "Design a FIFO.",
                            "file_path": "rtl/top.v",
                            "file_content": "module other; endmodule\n",
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(
                source,
                target,
                sample_id_prefix="sample_t0_t4_demo_",
                exclude_file_paths={"system_his.json"},
            )

            rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(count, 1)
            self.assertEqual(len(rows), 1)
            self.assertIn("Design a counter.", rows[0]["messages"][0]["content"])
            self.assertNotIn("system_his.json", rows[0]["messages"][0]["content"])
            self.assertNotIn("FIFO", rows[0]["messages"][0]["content"])

    def test_cli_filters_rows_by_sample_prefix_and_excluded_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirement_to_file.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        {
                            "sample_id": "sample_t0_t4_demo_000001",
                            "requirement": "Design a counter.",
                            "file_path": "rtl/top.v",
                            "file_content": "module top; endmodule\n",
                        },
                        {
                            "sample_id": "sample_t0_t4_demo_000001",
                            "requirement": "Design a counter.",
                            "file_path": "system_his.json",
                            "file_content": "{}\n",
                        },
                        {
                            "sample_id": "sample_other_000001",
                            "requirement": "Design a FIFO.",
                            "file_path": "rtl/top.v",
                            "file_content": "module other; endmodule\n",
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "sr2fpga_training.prepare_dataset",
                    "--input",
                    str(source),
                    "--output",
                    str(target),
                    "--sample-id-prefix",
                    "sample_t0_t4_demo_",
                    "--exclude-file-path",
                    "system_his.json",
                ],
                env={
                    **os.environ,
                    "PYTHONPATH": os.pathsep.join(
                        [
                            str(Path(__file__).resolve().parents[1] / "src"),
                            os.environ.get("PYTHONPATH", ""),
                        ]
                    ),
                },
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Converted 1 rows", result.stdout)
            rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertIn("rtl/top.v", rows[0]["messages"][0]["content"])

    def test_converts_project_to_predicted_qor_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "project_to_predicted_qor.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "files": [{"path": "rtl/top.v", "content": "module top; endmodule\n"}],
                        "predicted_qor": {"resources": {"lut": 4, "ff": 2}},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("Predict QoR", messages[0]["content"])
            self.assertIn("rtl/top.v", messages[0]["content"])
            self.assertEqual(json.loads(messages[1]["content"])["resources"]["lut"], 4)

    def test_converts_project_to_measured_qor_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "project_to_measured_qor.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "files": [{"path": "rtl/top.v", "content": "module top; endmodule\n"}],
                        "measured_qor": {"cell_count": 12, "tool": "yosys"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("Estimate measured QoR", messages[0]["content"])
            self.assertIn("rtl/top.v", messages[0]["content"])
            self.assertEqual(json.loads(messages[1]["content"])["cell_count"], 12)

    def test_converts_failure_to_diagnosis_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "failure_to_diagnosis.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "episode": {"attempts": [{"stage": "sim_run", "status": "failed"}]},
                        "diagnosis": {"failure_type": "functional_mismatch", "root_cause": "TEST_FAIL"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("Diagnose this SR2FPGA failure", messages[0]["content"])
            self.assertIn("sim_run", messages[0]["content"])
            self.assertEqual(json.loads(messages[1]["content"])["failure_type"], "functional_mismatch")

    def test_converts_failure_to_patch_training_view_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "failure_to_patch.jsonl"
            target = Path(tmp) / "train.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_demo",
                        "episode": {"attempts": [{"stage": "lint", "status": "failed"}]},
                        "diagnosis": {"failure_type": "lint_warning_as_error"},
                        "patch": "diff --git a/rtl/top.v b/rtl/top.v\n",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            count = convert_jsonl(source, target)

            self.assertEqual(count, 1)
            messages = json.loads(target.read_text(encoding="utf-8"))["messages"]
            self.assertIn("Patch this SR2FPGA failure", messages[0]["content"])
            self.assertIn("lint_warning_as_error", messages[0]["content"])
            self.assertEqual(messages[1]["content"], "diff --git a/rtl/top.v b/rtl/top.v")

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
