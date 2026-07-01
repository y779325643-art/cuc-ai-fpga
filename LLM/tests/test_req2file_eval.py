import json
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

from LLM.src.req2file_eval import (
    OpenAIChatCompletionsClient,
    assemble_predictions,
    build_eval_set,
    run_inference,
    score_predictions,
    verify_assembled_projects,
    verify_assembled_projects_with_synth,
    verify_assembled_projects_with_tools,
)
from LLM.src.sr2fpga_agent.models import ToolResult


class FakeReq2FileClient:
    def __init__(self) -> None:
        self.messages: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        file_path = messages[-1]["content"].split("File path:\n", 1)[1].strip()
        return f"// generated {file_path}\nmodule top; endmodule\n"


class FakeHTTPResponse:
    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps({"choices": [{"message": {"content": "module top; endmodule\n"}}]}).encode("utf-8")


class FakeCommandRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path, str]] = []

    def run(self, command: list[str], cwd: Path, stage: str, timeout_seconds: int = 30) -> ToolResult:
        self.calls.append((command, cwd, stage))
        stdout = "TEST_PASS\n" if stage == "sim_run" else ""
        return ToolResult(
            stage=stage,
            command=command,
            status="passed",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.01,
        )


class FakeSynthRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path, str, int]] = []

    def run(self, command: list[str], cwd: Path, stage: str, timeout_seconds: int = 30) -> ToolResult:
        self.calls.append((command, cwd, stage, timeout_seconds))
        return ToolResult(
            stage=stage,
            command=command,
            status="passed",
            exit_code=0,
            stdout="""
=== top ===

   Number of cells:                 12
     SB_LUT4                         5
     SB_DFF                          7
""",
            stderr="",
            duration_seconds=0.01,
        )


class Req2FileEvalTest(unittest.TestCase):
    def test_build_eval_set_filters_rows_and_writes_user_only_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirement_to_file.jsonl"
            target = Path(tmp) / "req2file_eval.jsonl"
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

            count = build_eval_set(
                source,
                target,
                sample_id_prefix="sample_t0_t4_demo_",
                exclude_file_paths={"system_his.json"},
            )

            rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(count, 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["sample_id"], "sample_t0_t4_demo_000001")
            self.assertEqual(rows[0]["file_path"], "rtl/top.v")
            self.assertEqual(rows[0]["expected_file_content"], "module top; endmodule\n")
            self.assertEqual(len(rows[0]["messages"]), 1)
            self.assertEqual(rows[0]["messages"][0]["role"], "user")
            self.assertIn("Generate this SR2FPGA project file", rows[0]["messages"][0]["content"])

    def test_score_predictions_reports_file_type_quality_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            predictions = Path(tmp) / "predictions.jsonl"
            predictions.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        {
                            "sample_id": "sample_1",
                            "file_path": "rtl/top.v",
                            "expected_file_content": "module top; endmodule\n",
                            "predicted_file_content": "module top; endmodule\n",
                        },
                        {
                            "sample_id": "sample_1",
                            "file_path": "manifest.json",
                            "expected_file_content": "{}\n",
                            "predicted_file_content": "{\"top_module\":\"top\"}\n",
                        },
                        {
                            "sample_id": "sample_1",
                            "file_path": "sim/tb_top.v",
                            "expected_file_content": "TEST_PASS\n",
                            "predicted_file_content": "initial begin if (ok) $display(\"TEST_PASS\"); else $display(\"TEST_FAIL\"); end\n",
                        },
                        {
                            "sample_id": "sample_1",
                            "file_path": "constraints/timing.sdc",
                            "expected_file_content": "",
                            "predicted_file_content": "create_clock -name clk -period 10.000 [get_ports clk]\n",
                        },
                        {
                            "sample_id": "sample_1",
                            "file_path": "reports/predicted_qor.json",
                            "expected_file_content": "{}\n",
                            "predicted_file_content": "{broken json",
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = score_predictions(predictions)

            self.assertEqual(report["rows"], 5)
            self.assertEqual(report["exact_match"], 1)
            self.assertEqual(report["non_empty"], 5)
            self.assertEqual(report["json_rows"], 2)
            self.assertEqual(report["json_valid"], 1)
            self.assertEqual(report["verilog_rows"], 2)
            self.assertEqual(report["verilog_module_present"], 1)
            self.assertEqual(report["testbench_rows"], 1)
            self.assertEqual(report["testbench_oracle_present"], 1)
            self.assertEqual(report["sdc_rows"], 1)
            self.assertEqual(report["sdc_clock_present"], 1)
            self.assertEqual(report["exact_match_ratio"], 0.2)
            self.assertEqual(report["json_valid_ratio"], 0.5)
            self.assertEqual(report["verilog_module_present_ratio"], 0.5)
            self.assertEqual(report["testbench_oracle_present_ratio"], 1.0)
            self.assertEqual(report["sdc_clock_present_ratio"], 1.0)

    def test_run_inference_writes_prediction_rows_with_model_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "eval.jsonl"
            predictions = Path(tmp) / "predictions.jsonl"
            eval_path.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_1",
                        "file_path": "rtl/top.v",
                        "requirement": "Design a counter.",
                        "messages": [
                            {
                                "role": "user",
                                "content": "Generate this SR2FPGA project file from the requirement.\n\n"
                                "SR2FPGA requirement:\nDesign a counter.\n\nFile path:\nrtl/top.v",
                            }
                        ],
                        "expected_file_content": "module top; endmodule\n",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            client = FakeReq2FileClient()

            count = run_inference(eval_path, predictions, client=client)

            rows = [json.loads(line) for line in predictions.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(count, 1)
            self.assertEqual(len(client.messages), 1)
            self.assertEqual(rows[0]["sample_id"], "sample_1")
            self.assertEqual(rows[0]["file_path"], "rtl/top.v")
            self.assertEqual(rows[0]["expected_file_content"], "module top; endmodule\n")
            self.assertIn("// generated rtl/top.v", rows[0]["predicted_file_content"])

    def test_openai_inference_client_omits_json_response_format_for_file_content(self) -> None:
        captured_payloads: list[dict[str, object]] = []

        def fake_urlopen(request, timeout):
            captured_payloads.append(json.loads(request.data.decode("utf-8")))
            return FakeHTTPResponse()

        client = OpenAIChatCompletionsClient(
            base_url="http://127.0.0.1:8000/v1",
            api_key="EMPTY",
            model="qwen-req2file",
            timeout_seconds=30,
            max_tokens=1024,
            temperature=0.0,
            transport_attempts=1,
        )

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            content = client.chat([{"role": "user", "content": "File path:\nrtl/top.v"}])

        self.assertEqual(content, "module top; endmodule\n")
        self.assertEqual(captured_payloads[0]["model"], "qwen-req2file")
        self.assertNotIn("response_format", captured_payloads[0])
        self.assertEqual(captured_payloads[0]["max_tokens"], 1024)

    def test_assemble_predictions_groups_files_and_backfills_reference_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            output_root = root / "assembled"
            reference_project = root / "reference/sample_1/final/generated_project"
            reference_project.mkdir(parents=True)
            (reference_project / "system_his.json").write_text('{"schema_version":"system-his-v1.2"}\n', encoding="utf-8")
            predictions.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        {
                            "sample_id": "sample_1",
                            "file_path": "manifest.json",
                            "expected_file_content": "",
                            "predicted_file_content": "{\"sources\":[\"rtl/top.v\"]}\n",
                        },
                        {
                            "sample_id": "sample_1",
                            "file_path": "rtl/top.v",
                            "expected_file_content": "",
                            "predicted_file_content": "module top; endmodule\n",
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = assemble_predictions(
                predictions,
                output_root,
                reference_dataset_root=root / "reference",
                backfill_reference_paths={"system_his.json"},
            )

            project_dir = output_root / "sample_1/generated_project"
            self.assertEqual(report["projects"], 1)
            self.assertEqual(report["written_files"], 2)
            self.assertEqual(report["backfilled_files"], 1)
            self.assertEqual((project_dir / "rtl/top.v").read_text(encoding="utf-8"), "module top; endmodule\n")
            self.assertTrue((project_dir / "system_his.json").exists())

    def test_verify_assembled_projects_reports_static_checks_for_oracle_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            output_root = root / "assembled"
            sample = Path("datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_counter_8_000001")
            rows = []
            for path in sorted((sample / "final/generated_project").rglob("*")):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(sample / "final/generated_project"))
                if rel == "system_his.json":
                    continue
                rows.append(
                    {
                        "sample_id": sample.name,
                        "file_path": rel,
                        "expected_file_content": path.read_text(encoding="utf-8"),
                        "predicted_file_content": path.read_text(encoding="utf-8"),
                    }
                )
            predictions.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            assemble_predictions(
                predictions,
                output_root,
                reference_dataset_root=Path("datasets/sr2fpga_rtl_v1"),
                backfill_reference_paths={"system_his.json"},
            )

            report = verify_assembled_projects(output_root)

            self.assertEqual(report["projects"], 1)
            self.assertEqual(report["l0_passed"], 1)
            self.assertEqual(report["rtl_identifier_passed"], 1)
            self.assertEqual(report["testbench_static_passed"], 1)
            self.assertEqual(report["project_results"][0]["sample_id"], sample.name)
            self.assertEqual(report["project_results"][0]["status"], "passed")

    def test_verify_assembled_projects_with_tools_runs_lint_and_simulation_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "assembled/sample_1/generated_project"
            (project_dir / "rtl").mkdir(parents=True)
            (project_dir / "sim").mkdir(parents=True)
            (project_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "top_module": "top",
                        "sources": ["rtl/top.v"],
                        "simulation": {"testbench": "sim/tb_top.v"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (project_dir / "rtl/top.v").write_text("module top; endmodule\n", encoding="utf-8")
            (project_dir / "sim/tb_top.v").write_text("module tb_top; endmodule\n", encoding="utf-8")
            runner = FakeCommandRunner()

            report = verify_assembled_projects_with_tools(root / "assembled", command_runner=runner)

            self.assertEqual(report["projects"], 1)
            self.assertEqual(report["lint_passed"], 1)
            self.assertEqual(report["sim_compile_passed"], 1)
            self.assertEqual(report["sim_run_passed"], 1)
            self.assertEqual([call[2] for call in runner.calls], ["lint", "sim_compile", "sim_run"])
            self.assertEqual(runner.calls[0][0], ["verilator", "--lint-only", "-Wall", "rtl/top.v"])
            self.assertIn("sim/tb_top.v", runner.calls[1][0])
            self.assertEqual(report["project_results"][0]["status"], "passed")

    def test_verify_assembled_projects_with_synth_runs_yosys_and_reports_qor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "assembled/sample_1/generated_project"
            (project_dir / "rtl").mkdir(parents=True)
            (project_dir / "manifest.json").write_text(
                json.dumps({"top_module": "top", "sources": ["rtl/top.v"]}) + "\n",
                encoding="utf-8",
            )
            (project_dir / "rtl/top.v").write_text("module top; endmodule\n", encoding="utf-8")
            runner = FakeSynthRunner()

            report = verify_assembled_projects_with_synth(root / "assembled", command_runner=runner)

            self.assertEqual(report["projects"], 1)
            self.assertEqual(report["synth_passed"], 1)
            self.assertEqual(report["project_results"][0]["status"], "passed")
            self.assertEqual(report["project_results"][0]["measured_qor"]["cell_count"], 12)
            self.assertEqual(report["project_results"][0]["measured_qor"]["cell_breakdown"]["SB_LUT4"], 5)
            self.assertEqual(runner.calls[0][2], "synth")
            self.assertEqual(runner.calls[0][3], 60)
            self.assertEqual(
                runner.calls[0][0],
                ["yosys", "-p", "read_verilog rtl/top.v; synth -top top; stat"],
            )


if __name__ == "__main__":
    unittest.main()
