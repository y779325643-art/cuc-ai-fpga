import json
import os
import unittest
from unittest import mock

from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekProjectGenerator,
    DeepSeekRepairer,
    _project_messages,
    _repair_messages,
    diff_projects,
    parse_project_files,
)
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


class DeepSeekProviderTest(unittest.TestCase):
    def test_parse_project_files_accepts_files_mapping(self) -> None:
        content = json.dumps(
            {
                "files": {
                    "system_his.json": "{}\n",
                    "manifest.json": _valid_manifest(),
                    "rtl/top.v": "module top; endmodule\n",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                    "sim/tb_top.v": "module tb_top; endmodule\n",
                    "reports/predicted_qor.json": "{}\n",
                }
            }
        )

        files = parse_project_files(content)

        self.assertEqual(files["rtl/top.v"], "module top; endmodule\n")
        self.assertEqual(len(files), 6)

    def test_parse_project_files_accepts_files_list(self) -> None:
        content = json.dumps(
            {
                "files": [
                    {"path": "system_his.json", "content": "{}\n"},
                    {"path": "manifest.json", "content": _valid_manifest()},
                    {"path": "rtl/top.v", "content": "module top; endmodule\n"},
                    {"path": "constraints/timing.sdc", "content": "create_clock -name clk -period 10 [get_ports clk]\n"},
                    {"path": "sim/tb_top.v", "content": "module tb_top; endmodule\n"},
                    {"path": "reports/predicted_qor.json", "content": "{}\n"},
                ]
            }
        )

        files = parse_project_files(content)

        self.assertEqual(files["rtl/top.v"], "module top; endmodule\n")
        self.assertEqual(files["sim/tb_top.v"], "module tb_top; endmodule\n")

    def test_parse_project_files_rejects_missing_required_file(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required files"):
            parse_project_files(json.dumps({"files": {"rtl/top.v": "module top; endmodule\n"}}))

    def test_parse_project_files_normalizes_trailing_newlines(self) -> None:
        content = json.dumps(
            {
                "files": {
                    "system_his.json": "{}",
                    "manifest.json": _valid_manifest().rstrip(),
                    "rtl/top.v": "module top; endmodule",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]",
                    "sim/tb_top.v": "module tb_top; endmodule",
                    "reports/predicted_qor.json": "{}",
                }
            }
        )

        files = parse_project_files(content)

        for file_content in files.values():
            self.assertTrue(file_content.endswith("\n"))

    def test_parse_project_files_rejects_manifest_without_pipeline_fields(self) -> None:
        content = json.dumps(
            {
                "files": {
                    "system_his.json": "{}\n",
                    "manifest.json": json.dumps({"files": ["rtl/top.v"]}) + "\n",
                    "rtl/top.v": "module top; endmodule\n",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                    "sim/tb_top.v": "module tb_top; endmodule\n",
                    "reports/predicted_qor.json": "{}\n",
                }
            }
        )

        with self.assertRaisesRegex(ValueError, "manifest.json missing required fields"):
            parse_project_files(content)

    def test_diff_projects_outputs_unified_diff_for_changed_files(self) -> None:
        old = GeneratedProject(
            project_name="demo",
            files={
                "rtl/top.v": "module top; assign out = 1'b0; endmodule\n",
                "manifest.json": _valid_manifest(),
            },
        )
        new = GeneratedProject(
            project_name="demo",
            files={
                "rtl/top.v": "module top; assign out = 1'b1; endmodule\n",
                "manifest.json": _valid_manifest(),
            },
        )

        patch = diff_projects(old, new)

        self.assertIn("--- a/rtl/top.v", patch)
        self.assertIn("+++ b/rtl/top.v", patch)
        self.assertIn("-module top; assign out = 1'b0; endmodule", patch)
        self.assertIn("+module top; assign out = 1'b1; endmodule", patch)
        self.assertNotIn("manifest.json", patch)

    def test_diff_projects_includes_added_and_deleted_files(self) -> None:
        old = GeneratedProject(project_name="demo", files={"old.v": "module old; endmodule\n"})
        new = GeneratedProject(project_name="demo", files={"new.v": "module new; endmodule\n"})

        patch = diff_projects(old, new)

        self.assertIn("--- a/old.v", patch)
        self.assertIn("+++ b/old.v", patch)
        self.assertIn("--- a/new.v", patch)
        self.assertIn("+++ b/new.v", patch)

    def test_deepseek_project_generator_uses_client_response(self) -> None:
        client = FakeDeepSeekClient(
            json.dumps(
                {
                    "files": {
                        "system_his.json": "{}\n",
                        "manifest.json": _valid_manifest(),
                        "rtl/top.v": "module top; endmodule\n",
                        "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                        "sim/tb_top.v": "module tb_top; endmodule\n",
                        "reports/predicted_qor.json": "{}\n",
                    }
                }
            )
        )
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = DeepSeekProjectGenerator(client=client).generate(request, platform)

        self.assertEqual(project.project_name, "counter_8bit")
        self.assertIn("rtl/top.v", project.files)
        self.assertEqual(client.call_count, 1)
        self.assertIn("counter_8bit", client.messages[1]["content"])

    def test_deepseek_project_generator_retries_after_invalid_response(self) -> None:
        client = FakeDeepSeekClient(
            [
                '{"files": {"system_his.json": "{}"',
                json.dumps(
                    {
                        "files": {
                            "system_his.json": "{}\n",
                            "manifest.json": _valid_manifest(),
                            "rtl/top.v": "module top; endmodule\n",
                            "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                            "sim/tb_top.v": "module tb_top; endmodule\n",
                            "reports/predicted_qor.json": "{}\n",
                        }
                    }
                ),
            ]
        )
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = DeepSeekProjectGenerator(client=client).generate(request, platform)

        self.assertIn("rtl/top.v", project.files)
        self.assertEqual(client.call_count, 2)

    def test_deepseek_repairer_uses_failure_context_and_returns_patch(self) -> None:
        original = GeneratedProject(
            project_name="counter_8bit",
            files={
                "system_his.json": "{}\n",
                "manifest.json": _valid_manifest(),
                "rtl/top.v": "module top(input wire clk); endmodule\n",
                "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                "sim/tb_top.v": "module tb_top; endmodule\n",
                "reports/predicted_qor.json": "{}\n",
            },
        )
        repaired_payload = json.dumps(
            {
                "files": {
                    "system_his.json": "{}\n",
                    "manifest.json": _valid_manifest(),
                    "rtl/top.v": "module top(input wire clk, input wire rst_n); endmodule\n",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                    "sim/tb_top.v": "module tb_top; endmodule\n",
                    "reports/predicted_qor.json": "{}\n",
                }
            }
        )
        client = FakeDeepSeekClient(repaired_payload)
        diagnosis = {
            "stage": "lint",
            "failure_type": "port_mismatch",
            "root_cause": "Port rst_n of module top is not declared",
            "affected_files": ["rtl/top.v"],
        }

        result = DeepSeekRepairer(client).repair(original, diagnosis)

        self.assertIn("rst_n", result.generated_project.files["rtl/top.v"])
        self.assertIn("--- a/rtl/top.v", result.patch_diff)
        self.assertIn("+++ b/rtl/top.v", result.patch_diff)
        self.assertIn("Port rst_n of module top is not declared", client.messages[1]["content"])
        self.assertIn("module top(input wire clk); endmodule", client.messages[1]["content"])

    def test_repair_prompt_requests_complete_project_package(self) -> None:
        project = GeneratedProject(
            project_name="counter_8bit",
            files={
                "manifest.json": _valid_manifest(),
                "rtl/top.v": "module top; endmodule\n",
            },
        )
        diagnosis = {"stage": "lint", "failure_type": "syntax_error", "root_cause": "syntax error"}

        messages = _repair_messages(project, diagnosis)
        prompt = messages[1]["content"]

        self.assertIn("Return JSON in this exact shape", prompt)
        self.assertIn('"manifest.json"', prompt)
        self.assertIn('"top_module": "top"', prompt)
        self.assertIn("syntax error", prompt)

    def test_project_prompt_requests_agent_manifest_schema(self) -> None:
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _project_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn('"top_module": "top"', user_prompt)
        self.assertIn('"sources": ["rtl/top.v"]', user_prompt)
        self.assertIn('"simulation": {"testbench": "sim/tb_top.v"}', user_prompt)

    def test_cli_builds_deepseek_generator_from_env_without_exposing_key(self) -> None:
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "secret-value"}):
            from LLM.src.sr2fpga_agent.cli import build_project_generator

            generator = build_project_generator(
                provider="deepseek",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
            )

        self.assertIsInstance(generator, DeepSeekProjectGenerator)

    def test_cli_passes_requirement_into_project_request(self) -> None:
        from LLM.src.sr2fpga_agent import cli

        captured = {}

        class FakeAgent:
            def __init__(
                self,
                dataset_root,
                project_generator=None,
                repairer=None,
                max_attempts=1,
            ) -> None:
                captured["dataset_root"] = dataset_root
                captured["project_generator"] = project_generator
                captured["repairer"] = repairer
                captured["max_attempts"] = max_attempts

            def run_one(self, sample_id, requirement, request, platform):
                captured["sample_id"] = sample_id
                captured["requirement"] = requirement
                captured["request"] = request
                captured["platform"] = platform
                return {"sample_dir": "datasets/sr2fpga_rtl_v1/sample_llm_000001", "pass_level": "L0"}

        requirement = "Design an 8-bit counter with enable, reset, and a self-checking testbench."
        with (
            mock.patch.object(cli, "DataGenerationAgent", FakeAgent),
            mock.patch.object(cli, "build_project_generator", return_value="fake-llm-generator"),
            mock.patch.object(cli, "build_repairer", return_value="fake-repairer"),
            mock.patch("builtins.print"),
        ):
            cli.main(
                [
                    "--dataset-root",
                    "datasets/sr2fpga_rtl_v1",
                    "--sample-id",
                    "sample_llm_000001",
                    "--provider",
                    "deepseek",
                    "--task-type",
                    "counter",
                    "--width",
                    "8",
                    "--project-name",
                    "llm_counter_8bit",
                    "--requirement",
                    requirement,
                    "--repair-provider",
                    "deepseek",
                    "--max-attempts",
                    "2",
                ]
            )

        self.assertEqual(captured["requirement"], requirement)
        self.assertEqual(captured["request"].description, requirement)
        self.assertEqual(captured["request"].task_type, "counter")
        self.assertEqual(captured["request"].width, 8)
        self.assertEqual(captured["request"].project_name, "llm_counter_8bit")
        self.assertEqual(captured["project_generator"], "fake-llm-generator")
        self.assertEqual(captured["repairer"], "fake-repairer")
        self.assertEqual(captured["max_attempts"], 2)

    def test_cli_builds_no_repairer_by_default(self) -> None:
        from LLM.src.sr2fpga_agent.cli import build_repairer

        repairer = build_repairer(
            provider="none",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
        )

        self.assertIsNone(repairer)

    def test_cli_builds_deepseek_repairer_from_env_without_exposing_key(self) -> None:
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "secret-value"}):
            from LLM.src.sr2fpga_agent.cli import build_repairer

            repairer = build_repairer(
                provider="deepseek",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
            )

        self.assertIsInstance(repairer, DeepSeekRepairer)

    def test_cli_rejects_non_positive_max_attempts(self) -> None:
        from LLM.src.sr2fpga_agent import cli

        with self.assertRaisesRegex(SystemExit, "--max-attempts must be >= 1"):
            cli.main(
                [
                    "--dataset-root",
                    "datasets/sr2fpga_rtl_v1",
                    "--sample-id",
                    "sample_bad_attempts",
                    "--provider",
                    "deterministic",
                    "--task-type",
                    "counter",
                    "--width",
                    "8",
                    "--project-name",
                    "bad_attempts",
                    "--max-attempts",
                    "0",
                ]
            )


class FakeDeepSeekClient:
    def __init__(self, content) -> None:
        self.content = content
        self.call_count = 0
        self.messages = []

    def chat(self, messages):
        self.call_count += 1
        self.messages = messages
        if isinstance(self.content, list):
            return self.content[self.call_count - 1]
        return self.content


def _valid_manifest() -> str:
    return (
        json.dumps(
            {
                "project_name": "counter_8bit",
                "top_module": "top",
                "sources": ["rtl/top.v"],
                "constraints": ["constraints/timing.sdc"],
                "simulation": {"testbench": "sim/tb_top.v"},
                "reports": ["reports/predicted_qor.json"],
            }
        )
        + "\n"
    )


if __name__ == "__main__":
    unittest.main()
