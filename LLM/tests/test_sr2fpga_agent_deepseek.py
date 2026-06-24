import json
import os
import unittest
from unittest import mock

from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekClient,
    DeepSeekConfig,
    DeepSeekHisProjectGenerator,
    DeepSeekProjectGenerator,
    DeepSeekRepairer,
    DeepSeekSystemHisGenerator,
    DeepSeekTwoStageProjectGenerator,
    _his_project_messages,
    _system_his_v12_messages,
    _project_messages,
    _repair_messages,
    diff_projects,
    parse_project_files,
    parse_system_his_v12,
)
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


class DeepSeekProviderTest(unittest.TestCase):
    def test_deepseek_client_passes_ssl_context_to_urlopen(self) -> None:
        ssl_context = object()
        response = FakeHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"files\": {}}"}}]}).encode("utf-8")
        )
        client = DeepSeekClient(
            DeepSeekConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=ssl_context),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=response) as urlopen,
        ):
            content = client.chat([{"role": "user", "content": "hello"}])

        self.assertEqual(content, '{"files": {}}')
        self.assertIs(urlopen.call_args.kwargs["context"], ssl_context)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 7)

    def test_deepseek_client_wraps_timeout_errors(self) -> None:
        client = DeepSeekClient(
            DeepSeekConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", side_effect=TimeoutError("timed out")),
        ):
            with self.assertRaisesRegex(RuntimeError, "DeepSeek API request timed out"):
                client.chat([{"role": "user", "content": "hello"}])

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

    def test_parse_system_his_v12_accepts_topdown_his_object(self) -> None:
        payload = _system_his_v12_fixture()

        system_his = parse_system_his_v12(json.dumps(payload))

        self.assertEqual(system_his["schema_version"], "system-his-v1.2-topdown")
        self.assertEqual(system_his["top"]["name"], "top")

    def test_parse_system_his_v12_accepts_wrapped_system_his_object(self) -> None:
        payload = {"system_his": _system_his_v12_fixture()}

        system_his = parse_system_his_v12(json.dumps(payload))

        self.assertEqual(system_his["schema_version"], "system-his-v1.2-topdown")

    def test_parse_system_his_v12_rejects_invalid_references(self) -> None:
        payload = _system_his_v12_fixture()
        payload["instances"][0]["component"] = "missing_component"

        with self.assertRaisesRegex(ValueError, "missing component 'missing_component'"):
            parse_system_his_v12(json.dumps(payload))

    def test_deepseek_system_his_generator_uses_short_prompt_and_checker(self) -> None:
        client = FakeDeepSeekClient(json.dumps(_system_his_v12_fixture()))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="生成一个 8-bit 双路数据流合并并累加的 FPGA RTL 工程",
        )
        platform = PlatformProfile(
            name="ac820_zynq",
            vendor="xilinx",
            family="zynq-7000",
            part="xc7z020clg484-2",
            board="AC820-ZYNQ",
            toolchain="openxc7",
        )

        system_his = DeepSeekSystemHisGenerator(client).generate(request, platform)

        self.assertEqual(system_his["schema_version"], "system-his-v1.2-topdown")
        self.assertEqual(client.call_count, 1)
        self.assertIn("生成一个 8-bit 双路数据流合并并累加", client.messages[1]["content"])
        self.assertIn("Return only System-HIS JSON", client.messages[1]["content"])
        self.assertIn("Do not generate RTL", client.messages[1]["content"])

    def test_deepseek_system_his_generator_retries_after_invalid_his(self) -> None:
        invalid = _system_his_v12_fixture()
        invalid["instances"][0]["component"] = "missing_component"
        client = FakeDeepSeekClient([json.dumps(invalid), json.dumps(_system_his_v12_fixture())])
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Build a dual stream join accumulator.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        system_his = DeepSeekSystemHisGenerator(client).generate(request, platform)

        self.assertEqual(system_his["schema_version"], "system-his-v1.2-topdown")
        self.assertEqual(client.call_count, 2)
        self.assertIn("previous System-HIS output failed validation", client.messages_history[1][-1]["content"])
        self.assertIn("missing component 'missing_component'", client.messages_history[1][-1]["content"])

    def test_system_his_v12_prompt_requests_topdown_architecture_contract(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _system_his_v12_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn("system-his-v1.2-topdown", user_prompt)
        self.assertIn("top", user_prompt)
        self.assertIn("state", user_prompt)
        self.assertIn("components", user_prompt)
        self.assertIn("instances", user_prompt)
        self.assertIn("data_flow", user_prompt)
        self.assertIn("control_flow", user_prompt)
        self.assertIn("component definitions from concrete instances", user_prompt)
        self.assertIn("Do not generate RTL", user_prompt)
        self.assertIn("Required architecture for composed_dual_stream_join", user_prompt)
        self.assertIn("components: skid_buffer, stream_join, accumulator_core, stream_stage", user_prompt)
        self.assertIn("instances: in0_buffer, in1_buffer, join_core, accumulator, out_stage", user_prompt)
        self.assertIn("Do not collapse this topology into one fused component", user_prompt)

    def test_deepseek_his_project_generator_uses_checked_his_contract(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeDeepSeekClient(json.dumps({"files": _project_files_for_system_his_v12(system_his)}))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = DeepSeekHisProjectGenerator(client).generate(request, platform, system_his)

        self.assertEqual(project.project_name, "join_8bit")
        self.assertIn("rtl/stream_join.v", project.files)
        self.assertEqual(client.call_count, 1)
        self.assertIn('"schema_version": "system-his-v1.2-topdown"', client.messages[1]["content"])
        self.assertIn("Do not change component, instance, top port, data_flow, or control_flow names", client.messages[1]["content"])

    def test_deepseek_his_project_generator_rejects_project_with_invalid_system_his(self) -> None:
        system_his = _system_his_v12_fixture()
        invalid_system_his = _system_his_v12_fixture()
        invalid_system_his["instances"][0]["component"] = "missing_component"
        files = _project_files_for_system_his_v12(invalid_system_his)
        client = FakeDeepSeekClient(json.dumps({"files": files}))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with self.assertRaisesRegex(ValueError, "DeepSeek HIS2PROJECT system_his.json failed validation"):
            DeepSeekHisProjectGenerator(client, max_attempts=1).generate(request, platform, system_his)

    def test_his_project_prompt_requires_complete_project_without_changing_his_contract(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _his_project_messages(request, platform, _system_his_v12_fixture())
        user_prompt = messages[1]["content"]

        self.assertIn("Generate a complete SR2FPGA Verilog RTL project from this checked System-HIS", user_prompt)
        self.assertIn("Do not change component, instance, top port, data_flow, or control_flow names", user_prompt)
        self.assertIn('"rtl/stream_join.v"', user_prompt)
        self.assertIn('"constraints": {"timing": "constraints/timing.sdc"}', user_prompt)

    def test_deepseek_two_stage_project_generator_runs_req2his_then_his2project(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeDeepSeekClient(
            [
                json.dumps(system_his),
                json.dumps({"files": _project_files_for_system_his_v12(system_his)}),
            ]
        )
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = DeepSeekTwoStageProjectGenerator(client).generate(request, platform)

        self.assertEqual(project.project_name, "join_8bit")
        self.assertIn("rtl/stream_join.v", project.files)
        self.assertEqual(client.call_count, 2)
        self.assertIn("Generate a System-HIS v1.2", client.messages_history[0][1]["content"])
        self.assertIn("Generate a complete SR2FPGA Verilog RTL project", client.messages_history[1][1]["content"])

    def test_deepseek_two_stage_project_generator_emits_stage_events(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeDeepSeekClient(
            [
                json.dumps(system_his),
                json.dumps({"files": _project_files_for_system_his_v12(system_his)}),
            ]
        )
        events = []
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        DeepSeekTwoStageProjectGenerator(client, event_sink=events.append).generate(request, platform)

        self.assertEqual(
            [event["event"] for event in events],
            [
                "generation_stage_started",
                "generation_stage_finished",
                "generation_stage_started",
                "generation_stage_finished",
            ],
        )
        self.assertEqual([event["stage"] for event in events], ["req2his", "req2his", "his2project", "his2project"])
        self.assertEqual({event["project_name"] for event in events}, {"join_8bit"})
        self.assertEqual({event["task_type"] for event in events}, {"composed_dual_stream_join"})
        self.assertTrue(all("duration_seconds" in event for event in events if event["event"].endswith("finished")))

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

    def test_deepseek_project_generator_retries_single_file_multimodule_response(self) -> None:
        single_file_payload = json.dumps(
            {
                "files": {
                    "system_his.json": json.dumps({"task_type": "uart_tx"}) + "\n",
                    "manifest.json": _valid_manifest(),
                    "rtl/top.v": "module top; endmodule\n",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                    "sim/tb_top.v": "module tb_top; initial $display(\"TEST_PASS\"); endmodule\n",
                    "reports/predicted_qor.json": "{}\n",
                }
            }
        )
        multi_file_payload = json.dumps(
            {
                "files": {
                    "system_his.json": json.dumps({"task_type": "uart_tx"}) + "\n",
                    "manifest.json": _valid_manifest(
                        sources=["rtl/top.v", "rtl/baud_tick_gen.v", "rtl/uart_tx_core.v"]
                    ),
                    "rtl/top.v": "module top; baud_tick_gen u_tick(); uart_tx_core u_core(); endmodule\n",
                    "rtl/baud_tick_gen.v": "module baud_tick_gen; endmodule\n",
                    "rtl/uart_tx_core.v": "module uart_tx_core; endmodule\n",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                    "sim/tb_top.v": "module tb_top; initial $display(\"TEST_PASS\"); endmodule\n",
                    "reports/predicted_qor.json": "{}\n",
                }
            }
        )
        client = FakeDeepSeekClient([single_file_payload, multi_file_payload])
        request = ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = DeepSeekProjectGenerator(client=client).generate(request, platform)

        manifest = json.loads(project.files["manifest.json"])
        self.assertEqual(client.call_count, 2)
        self.assertEqual(
            manifest["sources"],
            ["rtl/top.v", "rtl/baud_tick_gen.v", "rtl/uart_tx_core.v"],
        )
        self.assertIn("rtl/uart_tx_core.v", project.files)

    def test_parse_project_files_rejects_single_file_composed_topology_response(self) -> None:
        content = json.dumps(
            {
                "files": {
                    "system_his.json": json.dumps({"task_type": "composed_dual_stream_join"}) + "\n",
                    "manifest.json": _valid_manifest(),
                    "rtl/top.v": "module top; endmodule\n",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                    "sim/tb_top.v": "module tb_top; initial $display(\"TEST_PASS\"); endmodule\n",
                    "reports/predicted_qor.json": "{}\n",
                }
            }
        )

        with self.assertRaisesRegex(ValueError, "must include rtl/top.v and at least two submodule"):
            parse_project_files(content, expected_task_type="composed_dual_stream_join")

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

    def test_deepseek_repairer_preserves_valid_unrelated_manifest(self) -> None:
        original_manifest = json.dumps(
            {
                "project_name": "counter_8bit",
                "top_module": "top",
                "language": "verilog",
                "target": {"vendor": "generic", "toolchain": "open_source"},
                "sources": ["rtl/top.v"],
                "constraints": {"timing": "constraints/timing.sdc"},
                "simulation": {"testbench": "sim/tb_top.v", "type": "self_checking"},
                "reports": {"predicted_qor": "reports/predicted_qor.json"},
            },
            indent=2,
        ) + "\n"
        original = GeneratedProject(
            project_name="counter_8bit",
            files={
                "system_his.json": "{}\n",
                "manifest.json": original_manifest,
                "rtl/top.v": "module top(input wire clk, input wire reset_n); endmodule\n",
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
            "failure_type": "reset_behavior_error",
            "root_cause": "rtl/top.v: Port rst_n of module top is not declared",
            "affected_files": ["rtl/top.v"],
        }

        result = DeepSeekRepairer(client).repair(original, diagnosis)

        self.assertEqual(result.generated_project.files["manifest.json"], original_manifest)
        self.assertIn("--- a/rtl/top.v", result.patch_diff)
        self.assertNotIn("manifest.json", result.patch_diff)

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
        self.assertIn("system-his-v1.1", prompt)
        self.assertIn('"project": {', prompt)
        self.assertIn('"project_name": "counter_8bit"', prompt)
        self.assertIn('"name": "counter_8bit"', prompt)
        self.assertIn('"clocks": [', prompt)
        self.assertIn('"name": "clk"', prompt)
        self.assertIn('"role": "top"', prompt)
        self.assertIn('"role": "submodule"', prompt)
        self.assertIn('"clock": "clk"', prompt)
        self.assertIn('"parameters": {', prompt)
        self.assertIn('"WIDTH": 8', prompt)
        self.assertIn('"params": [', prompt)
        self.assertIn('"value": 8', prompt)
        self.assertIn('"protocol": "register"', prompt)
        self.assertIn('"constraints": {"timing": "constraints/timing.sdc"}', prompt)
        self.assertIn("Do not use Verilog reserved keywords as any RTL identifier", prompt)
        self.assertIn("connection endpoint module values must use System-HIS module names", prompt)
        self.assertIn("not instance aliases such as sb0, join, acc, or stg", prompt)
        self.assertIn("width strings must match parsed RTL ranges exactly", prompt)
        self.assertIn('"modules": [', prompt)
        self.assertIn('"connections": [', prompt)
        self.assertIn('"top_ports": [', prompt)
        self.assertIn('"verification": {', prompt)
        self.assertIn('"testbench": "sim/tb_top.v"', prompt)
        self.assertIn('"qor_intent": {', prompt)
        self.assertIn('"resources": {', prompt)
        self.assertIn("Preserve every file that is not needed", prompt)
        self.assertIn("syntax error", prompt)

    def test_project_prompt_requests_agent_manifest_schema(self) -> None:
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _project_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn('"top_module": "top"', user_prompt)
        self.assertIn('"sources": ["rtl/top.v"]', user_prompt)
        self.assertIn('"constraints": {"timing": "constraints/timing.sdc"}', user_prompt)
        self.assertIn('"simulation": {"testbench": "sim/tb_top.v"}', user_prompt)

    def test_project_prompt_requests_true_multifile_rtl_for_multimodule_tasks(self) -> None:
        request = ProjectRequest(task_type="spi_master", width=8, project_name="spi_master_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _project_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn("Generate a true multi-file RTL implementation", user_prompt)
        self.assertIn("rtl/top.v must be an integration wrapper", user_prompt)
        self.assertIn('"rtl/clock_divider.v"', user_prompt)
        self.assertIn('"rtl/spi_master_core.v"', user_prompt)
        self.assertIn('"rtl/clock_divider.v": "..."', user_prompt)
        self.assertIn('"rtl/spi_master_core.v": "..."', user_prompt)
        self.assertIn('"sources": ["rtl/top.v", "rtl/clock_divider.v", "rtl/spi_master_core.v"]', user_prompt)

    def test_project_prompt_requests_true_multifile_rtl_for_composed_topology_tasks(self) -> None:
        request = ProjectRequest(task_type="composed_dual_stream_join", width=8, project_name="join_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _project_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn("Generate a true multi-file RTL implementation", user_prompt)
        self.assertIn("rtl/top.v must be an integration wrapper", user_prompt)
        self.assertIn('"rtl/skid_buffer.v"', user_prompt)
        self.assertIn('"rtl/stream_join.v"', user_prompt)
        self.assertIn('"rtl/accumulator_core.v"', user_prompt)
        self.assertIn('"rtl/stream_stage.v"', user_prompt)
        self.assertIn(
            (
                '"sources": ["rtl/top.v", "rtl/skid_buffer.v", "rtl/stream_join.v", '
                '"rtl/accumulator_core.v", "rtl/stream_stage.v"]'
            ),
            user_prompt,
        )

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

    def test_cli_builds_deepseek_his_v12_two_stage_generator_from_env(self) -> None:
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "secret-value"}):
            from LLM.src.sr2fpga_agent.cli import build_project_generator

            generator = build_project_generator(
                provider="deepseek-his-v12",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
            )

        self.assertIsInstance(generator, DeepSeekTwoStageProjectGenerator)

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
        self.messages_history = []

    def chat(self, messages):
        self.call_count += 1
        self.messages = messages
        self.messages_history.append(messages)
        if isinstance(self.content, list):
            return self.content[self.call_count - 1]
        return self.content


class FakeHTTPResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self.body


def _valid_manifest(sources=None) -> str:
    if sources is None:
        sources = ["rtl/top.v"]
    return (
        json.dumps(
            {
                "project_name": "counter_8bit",
                "top_module": "top",
                "sources": sources,
                "constraints": ["constraints/timing.sdc"],
                "simulation": {"testbench": "sim/tb_top.v"},
                "reports": ["reports/predicted_qor.json"],
            }
        )
        + "\n"
    )


def _system_his_v12_fixture() -> dict[str, object]:
    with open("docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json", encoding="utf-8") as handle:
        return json.load(handle)


def _project_files_for_system_his_v12(system_his: dict[str, object]) -> dict[str, str]:
    return {
        "system_his.json": json.dumps(system_his, indent=2) + "\n",
        "manifest.json": _valid_manifest(
            sources=[
                "rtl/top.v",
                "rtl/skid_buffer.v",
                "rtl/stream_join.v",
                "rtl/accumulator_core.v",
                "rtl/stream_stage.v",
            ]
        ),
        "rtl/top.v": "module top; skid_buffer in0_buffer(); stream_join join_core(); endmodule\n",
        "rtl/skid_buffer.v": "module skid_buffer; endmodule\n",
        "rtl/stream_join.v": "module stream_join; endmodule\n",
        "rtl/accumulator_core.v": "module accumulator_core; endmodule\n",
        "rtl/stream_stage.v": "module stream_stage; endmodule\n",
        "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
        "sim/tb_top.v": "module tb_top; initial $display(\"TEST_PASS\"); endmodule\n",
        "reports/predicted_qor.json": "{}\n",
    }


if __name__ == "__main__":
    unittest.main()
