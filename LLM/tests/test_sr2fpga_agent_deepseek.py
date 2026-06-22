import json
import os
import unittest
from unittest import mock

from LLM.src.sr2fpga_agent.deepseek import DeepSeekProjectGenerator, parse_project_files
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest


class DeepSeekProviderTest(unittest.TestCase):
    def test_parse_project_files_accepts_files_mapping(self) -> None:
        content = json.dumps(
            {
                "files": {
                    "system_his.json": "{}\n",
                    "manifest.json": "{}\n",
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

    def test_parse_project_files_rejects_missing_required_file(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required files"):
            parse_project_files(json.dumps({"files": {"rtl/top.v": "module top; endmodule\n"}}))

    def test_deepseek_project_generator_uses_client_response(self) -> None:
        client = FakeDeepSeekClient(
            json.dumps(
                {
                    "files": {
                        "system_his.json": "{}\n",
                        "manifest.json": "{\"top_module\":\"top\"}\n",
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
            def __init__(self, dataset_root, project_generator=None) -> None:
                captured["dataset_root"] = dataset_root
                captured["project_generator"] = project_generator

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
                ]
            )

        self.assertEqual(captured["requirement"], requirement)
        self.assertEqual(captured["request"].description, requirement)
        self.assertEqual(captured["request"].task_type, "counter")
        self.assertEqual(captured["request"].width, 8)
        self.assertEqual(captured["request"].project_name, "llm_counter_8bit")
        self.assertEqual(captured["project_generator"], "fake-llm-generator")


class FakeDeepSeekClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.call_count = 0
        self.messages = []

    def chat(self, messages):
        self.call_count += 1
        self.messages = messages
        return self.content


if __name__ == "__main__":
    unittest.main()
