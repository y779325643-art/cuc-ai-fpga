import json
import http.client
import os
import unittest
import urllib.error
from unittest import mock

from LLM.src.sr2fpga_agent.deepseek import (
    AnthropicCompatibleClient,
    AnthropicCompatibleConfig,
    DeepSeekHisProjectGenerator,
    DeepSeekOracleHisProjectGenerator,
    DeepSeekProjectGenerator,
    DeepSeekRepairer,
    DeepSeekSystemHisGenerator,
    DeepSeekTwoStageProjectGenerator,
    OpenAICompatibleClient,
    OpenAICompatibleConfig,
    _his_project_messages,
    _system_his_v12_messages,
    _with_his_project_retry_feedback,
    _with_system_his_retry_feedback,
    _project_messages,
    _repair_messages,
    diff_projects,
    parse_project_files,
    parse_system_his_v12,
)
from LLM.src.sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator


class DeepSeekProviderTest(unittest.TestCase):
    def test_anthropic_compatible_client_uses_official_messages_headers(self) -> None:
        response = FakeHTTPResponse(
            json.dumps({"content": [{"type": "text", "text": "{\"ok\": true}"}]}).encode("utf-8")
        )
        client = AnthropicCompatibleClient(
            AnthropicCompatibleConfig(
                api_key="fake-key",
                model="claude-opus-4-8",
                base_url="https://w.ciykj.cn/v1",
                timeout_seconds=7,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=response) as urlopen,
        ):
            content = client.chat(
                [
                    {"role": "system", "content": "Return strict JSON."},
                    {"role": "user", "content": "Return ok."},
                ]
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://w.ciykj.cn/v1/messages")
        self.assertEqual(request.headers["X-api-key"], "fake-key")
        self.assertEqual(request.headers["Anthropic-version"], "2023-06-01")
        self.assertEqual(payload["system"], "Return strict JSON.")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "Return ok."}])
        self.assertEqual(content, '{"ok": true}')

    def test_openai_compatible_client_passes_ssl_context_to_urlopen(self) -> None:
        ssl_context = object()
        response = FakeHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"files\": {}}"}}]}).encode("utf-8")
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
                transport_attempts=1,
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

    def test_openai_compatible_client_wraps_timeout_errors(self) -> None:
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
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
            with self.assertRaisesRegex(RuntimeError, "OpenAI-compatible API request timed out"):
                client.chat([{"role": "user", "content": "hello"}])

    def test_openai_compatible_client_times_out_never_ending_response_body(self) -> None:
        response = FakeNeverEndingHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=1,
                transport_attempts=1,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=response),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.time.monotonic", side_effect=[0.0, 0.0, 2.0]),
        ):
            with self.assertRaisesRegex(RuntimeError, "OpenAI-compatible API response read timed out"):
                client.chat([{"role": "user", "content": "hello"}])

    def test_openai_compatible_client_classifies_reader_timeout_as_response_read_timeout(self) -> None:
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
                transport_attempts=1,
            )
        )

        def timed_out_reader(_response):
            raise TimeoutError("read deadline exceeded")

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=FakeHTTPResponse(b"{}")),
        ):
            with self.assertRaisesRegex(RuntimeError, "OpenAI-compatible API response read timed out"):
                client._request_with_retries({"messages": []}, timed_out_reader)

    def test_openai_compatible_client_retries_transient_http_errors(self) -> None:
        response = FakeHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")
        )
        transient_error = urllib.error.HTTPError(
            url="https://api.deepseek.example/chat/completions",
            code=502,
            msg="Bad Gateway",
            hdrs=None,
            fp=FakeHTTPResponse(b'{"error":"upstream"}'),
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
                transport_attempts=2,
                retry_backoff_seconds=0,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch(
                "LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen",
                side_effect=[transient_error, response],
            ) as urlopen,
        ):
            content = client.chat([{"role": "user", "content": "hello"}])

        self.assertEqual(content, '{"ok": true}')
        self.assertEqual(urlopen.call_count, 2)

    def test_openai_compatible_client_retries_incomplete_read(self) -> None:
        response = FakeHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
                transport_attempts=2,
                retry_backoff_seconds=0,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch(
                "LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen",
                side_effect=[http.client.IncompleteRead(b"partial"), response],
            ) as urlopen,
        ):
            content = client.chat([{"role": "user", "content": "hello"}])

        self.assertEqual(content, '{"ok": true}')
        self.assertEqual(urlopen.call_count, 2)

    def test_openai_compatible_client_omits_response_format_for_claude_models(self) -> None:
        response = FakeHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="claude-opus-4-5-20251101",
                base_url="https://api.claude.example",
                timeout_seconds=7,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=response) as urlopen,
        ):
            content = client.chat([{"role": "user", "content": "hello"}])

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(content, '{"ok": true}')
        self.assertNotIn("response_format", payload)

    def test_openai_compatible_client_includes_max_tokens_when_configured(self) -> None:
        response = FakeHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
                max_tokens=4096,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=response) as urlopen,
        ):
            content = client.chat([{"role": "user", "content": "hello"}])

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(content, '{"ok": true}')
        self.assertEqual(payload["max_tokens"], 4096)

    def test_openai_compatible_client_merges_system_messages_for_claude_models(self) -> None:
        response = FakeHTTPResponse(
            json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="claude-opus-4-8",
                base_url="https://api.claude.example",
                timeout_seconds=7,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=response) as urlopen,
        ):
            content = client.chat(
                [
                    {"role": "system", "content": "Use strict JSON."},
                    {"role": "user", "content": "Return ok."},
                ]
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(content, '{"ok": true}')
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertIn("Use strict JSON.", payload["messages"][0]["content"])
        self.assertIn("Return ok.", payload["messages"][0]["content"])
        self.assertFalse(any(message["role"] == "system" for message in payload["messages"]))

    def test_openai_compatible_client_stream_chat_parses_sse_delta_content(self) -> None:
        ssl_context = object()
        response = FakeStreamingHTTPResponse(
            [
                b": keep-alive\n",
                b"\n",
                b'data: {"choices":[{"delta":{"content":"{\\"files\\":"}}]}\n',
                b'data: {"choices":[{"delta":{"content":" {}}"}}]}\n',
                b"data: [DONE]\n",
            ]
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
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
            content = client.stream_chat([{"role": "user", "content": "hello"}])

        self.assertEqual(content, '{"files": {}}')
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertTrue(payload["stream"])
        self.assertIs(urlopen.call_args.kwargs["context"], ssl_context)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 7)

    def test_openai_compatible_client_stream_chat_ignores_metadata_chunks(self) -> None:
        response = FakeStreamingHTTPResponse(
            [
                b'data: {"id":"chunk-1","object":"chat.completion.chunk","choices":[]}\n',
                b'data: {"choices":[{"delta":{"content":"{\\"files\\":"}}]}\n',
                b'data: {"usage":{"prompt_tokens":1,"completion_tokens":1}}\n',
                b'data: {"choices":[{"delta":{"content":" {}}"}}]}\n',
                b"data: [DONE]\n",
            ]
        )
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key="fake-key",
                model="deepseek-test",
                base_url="https://api.deepseek.example",
                timeout_seconds=7,
            )
        )

        with (
            mock.patch("LLM.src.sr2fpga_agent.deepseek._default_ssl_context", return_value=object()),
            mock.patch("LLM.src.sr2fpga_agent.deepseek.urllib.request.urlopen", return_value=response),
        ):
            content = client.stream_chat([{"role": "user", "content": "hello"}])

        self.assertEqual(content, '{"files": {}}')

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
        client = FakeChatClient(
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

    def test_parse_system_his_v12_accepts_canonical_his_object(self) -> None:
        payload = _system_his_v12_fixture()

        system_his = parse_system_his_v12(json.dumps(payload))

        self.assertEqual(system_his["schema_version"], "system-his-v1.2")
        self.assertEqual(system_his["top"]["name"], "top")

    def test_parse_system_his_v12_accepts_wrapped_system_his_object(self) -> None:
        payload = {"system_his": _system_his_v12_fixture()}

        system_his = parse_system_his_v12(json.dumps(payload))

        self.assertEqual(system_his["schema_version"], "system-his-v1.2")

    def test_parse_system_his_v12_rejects_invalid_references(self) -> None:
        payload = _system_his_v12_fixture()
        payload["instances"][0]["component"] = "missing_component"

        with self.assertRaisesRegex(ValueError, "missing component 'missing_component'"):
            parse_system_his_v12(json.dumps(payload))

    def test_deepseek_system_his_generator_uses_short_prompt_and_checker(self) -> None:
        client = FakeChatClient(json.dumps(_system_his_v12_fixture()))
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

        self.assertEqual(system_his["schema_version"], "system-his-v1.2")
        self.assertEqual(client.call_count, 1)
        self.assertEqual(client.stream_call_count, 1)
        self.assertEqual(client.chat_call_count, 0)
        self.assertIn("生成一个 8-bit 双路数据流合并并累加", client.messages[1]["content"])
        self.assertIn("Return only System-HIS JSON", client.messages[1]["content"])
        self.assertIn("Do not generate RTL", client.messages[1]["content"])

    def test_deepseek_system_his_generator_retries_after_invalid_his(self) -> None:
        invalid = _system_his_v12_fixture()
        invalid["instances"][0]["component"] = "missing_component"
        client = FakeChatClient([json.dumps(invalid), json.dumps(_system_his_v12_fixture())])
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Build a dual stream join accumulator.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        system_his = DeepSeekSystemHisGenerator(client).generate(request, platform)

        self.assertEqual(system_his["schema_version"], "system-his-v1.2")
        self.assertEqual(client.call_count, 2)
        self.assertIn("previous System-HIS output failed validation", client.messages_history[1][-1]["content"])
        self.assertIn("missing component 'missing_component'", client.messages_history[1][-1]["content"])

    def test_deepseek_system_his_generator_retries_after_req_fidelity_mismatch(self) -> None:
        mismatched_system_his = _system_his_v12_fixture()
        corrected_system_his = _deterministic_system_his(
            ProjectRequest(
                task_type="composed_event_counter",
                width=8,
                project_name="event_counter_8bit",
                description="Build an event counter.",
            )
        )
        client = FakeChatClient([json.dumps(mismatched_system_his), json.dumps(corrected_system_his)])
        request = ProjectRequest(
            task_type="composed_event_counter",
            width=8,
            project_name="event_counter_8bit",
            description="Build an event counter.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        system_his = DeepSeekSystemHisGenerator(client).generate(request, platform)

        self.assertEqual(system_his["top"]["name"], "top")
        self.assertEqual(client.call_count, 2)
        self.assertIn("REQ2HIS fidelity", client.messages_history[1][-1]["content"])
        self.assertIn("composed_event_counter requires component 'event_gate'", client.messages_history[1][-1]["content"])

    def test_system_his_retry_feedback_includes_previous_json_and_ir_repair_rules(self) -> None:
        invalid = _system_his_v12_fixture()
        invalid["instances"][0].pop("name")
        invalid["data_flow"][0]["path"][1] = "skid_buffer.in_data"
        invalid["control_flow"].append(
            {
                "name": "bad_effect",
                "kind": "handshake_rule",
                "when": {"signal": "top.in0_valid", "op": "==", "value": 1},
                "effect": {"action": "assert", "target": "top.out_valid"},
                "related_state": [],
                "related_flows": [],
            }
        )
        client = FakeChatClient([json.dumps(invalid), json.dumps(_system_his_v12_fixture())])
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Build a dual stream join accumulator.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        DeepSeekSystemHisGenerator(client).generate(request, platform)

        retry_prompt = client.messages_history[1][-1]["content"]
        self.assertIn("Previous invalid System-HIS JSON", retry_prompt)
        self.assertIn('"component": "skid_buffer"', retry_prompt)
        self.assertIn("Every instances[] object must include name", retry_prompt)
        self.assertIn("Every instances[].owns_state must be a JSON array", retry_prompt)
        self.assertIn("top.clocks[].target_fmax_mhz and timing.target_fmax_mhz must be positive numbers", retry_prompt)
        self.assertIn("data_flow.path endpoints must use top.<port> or <instance>.<port>", retry_prompt)
        self.assertIn("effect.target must reference a declared data_flow name or state name", retry_prompt)

    def test_system_his_v12_prompt_requests_canonical_architecture_contract(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _system_his_v12_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn("system-his-v1.2", user_prompt)
        self.assertNotIn("system-his-v1.2-topdown", user_prompt)
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
        self.assertIn("Every clock and reset declared in top.clocks/top.resets must also appear in top.ports", user_prompt)
        self.assertIn("Every instances[].parameter_values key must be declared in that component's parameters", user_prompt)
        self.assertIn("Every components[].source must be one of artifacts.rtl_sources", user_prompt)
        self.assertIn('Do not use placeholder sources such as "library"', user_prompt)
        self.assertIn("Every instances[].owns_state must be a JSON array", user_prompt)
        self.assertIn("top.clocks[].target_fmax_mhz and timing.target_fmax_mhz must be positive numbers", user_prompt)
        self.assertIn("Every state.fsms[] entry must declare owner or use <instance>.<fsm> naming", user_prompt)
        self.assertIn("FSM owner must be top or an instances[].name", user_prompt)
        self.assertIn("State names across registers, counters, fsms, buffers, and memories must be globally unique", user_prompt)
        self.assertIn("control_flow.effect.target must reference a declared data_flow name or state name", user_prompt)

    def test_system_his_v12_prompt_requests_timing_and_structured_control_contract(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _system_his_v12_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn("data_flow.timing", user_prompt)
        self.assertIn("when", user_prompt)
        self.assertIn("effect", user_prompt)
        self.assertIn("guard", user_prompt)
        self.assertIn("depth <= 2", user_prompt)

    def test_system_his_v12_prompt_spells_out_reset_schema_enums(self) -> None:
        request = ProjectRequest(
            task_type="composed_stream_accumulator",
            width=8,
            project_name="accum_8bit",
            description="Generate a stream accumulator.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("top.resets[].polarity must be active_low or active_high", user_prompt)
        self.assertIn("top.resets[].kind must be sync or async", user_prompt)
        self.assertIn('Use {"name": "rst_n", "polarity": "active_low"', user_prompt)

    def test_system_his_v12_initial_prompt_spells_out_stream_accumulator_contract(self) -> None:
        request = ProjectRequest(
            task_type="composed_stream_accumulator",
            width=8,
            project_name="accum_8bit",
            description="Generate a stream accumulator.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_stream_accumulator", user_prompt)
        self.assertIn("components: skid_buffer, accumulator_core", user_prompt)
        self.assertIn("top ports must include clk, rst_n, in_valid, in_data, in_ready, sample_valid, and sum", user_prompt)
        self.assertIn("accumulator_core ports must be clk, rst_n, sample_valid, sample, sample_ready, and sum", user_prompt)
        self.assertIn("Do not introduce sample_valid_in", user_prompt)
        self.assertIn("accumulator.sample_valid to top.sample_valid", user_prompt)

    def test_system_his_v12_prompt_spells_out_join_ready_valid_and_timing_contract(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("data_flow.timing entries must use concrete integer latency_cycles", user_prompt)
        self.assertIn("join_core.out_valid, accumulator.sample_valid", user_prompt)
        self.assertIn("out_stage.in_ready, accumulator.sample_ready", user_prompt)
        self.assertIn("Do not introduce accumulator_core sample_valid_in", user_prompt)

    def test_system_his_v12_prompt_spells_out_stream_fork_contract(self) -> None:
        request = ProjectRequest(
            task_type="composed_stream_fork",
            width=8,
            project_name="fork_8bit",
            description="Generate a stream fork.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("top ports must include clk, rst_n, in_valid, in_data, in_ready, out0_valid", user_prompt)
        self.assertIn("both output payload paths and the corresponding valid/ready paths", user_prompt)

    def test_system_his_v12_prompt_includes_vector_mac_pipeline_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_vector_mac_pipeline",
            width=8,
            project_name="vector_mac_8bit",
            description="Generate a vector MAC feature pipeline.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_vector_mac_pipeline", user_prompt)
        self.assertIn("vector_mac_core", user_prompt)
        self.assertIn("feature_buffer", user_prompt)
        self.assertIn("weight_buffer", user_prompt)
        self.assertIn("mac_core_fsm is used, declare it with owner mac_core", user_prompt)
        self.assertIn("states IDLE/ACCUMULATE/OUTPUT, initial IDLE, reset_state IDLE", user_prompt)
        self.assertIn("rtl/vector_mac_core.v", user_prompt)

    def test_system_his_v12_prompt_includes_td_update_core_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_td_update_core",
            width=8,
            project_name="td_update_8bit",
            description="Generate a TD update core.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_td_update_core", user_prompt)
        self.assertIn("td_input_stage", user_prompt)
        self.assertIn("discount_core", user_prompt)
        self.assertIn("td_update_core", user_prompt)
        self.assertIn("output_stage FSM is used, declare it with owner output_stage", user_prompt)
        self.assertIn("states IDLE/VALID, initial IDLE, reset_state IDLE", user_prompt)
        self.assertIn("rtl/td_update_core.v", user_prompt)

    def test_system_his_v12_prompt_includes_policy_value_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_policy_value_shell",
            width=8,
            project_name="policy_value_shell_8bit",
            description="Generate a policy/value shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_policy_value_shell", user_prompt)
        self.assertIn("config_reg_bank", user_prompt)
        self.assertIn("observation_stage", user_prompt)
        self.assertIn("policy_score_core", user_prompt)
        self.assertIn("action_select_core", user_prompt)
        self.assertIn("rtl/action_select_core.v", user_prompt)

    def test_system_his_v12_prompt_includes_replay_sample_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_replay_sample_shell",
            width=8,
            project_name="replay_sample_shell_8bit",
            description="Generate a replay sample shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_replay_sample_shell", user_prompt)
        self.assertIn("host_sample_stage", user_prompt)
        self.assertIn("replay_store", user_prompt)
        self.assertIn("sample_pack_core", user_prompt)
        self.assertIn("sample_read_stage", user_prompt)
        self.assertIn("rtl/replay_store.v", user_prompt)

    def test_system_his_v12_prompt_includes_host_protocol_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_host_protocol_shell",
            width=8,
            project_name="host_protocol_shell_8bit",
            description="Generate a host protocol shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_host_protocol_shell", user_prompt)
        self.assertIn("axi_lite_write_ctrl", user_prompt)
        self.assertIn("axi_lite_read_ctrl", user_prompt)
        self.assertIn("control_reg_bank", user_prompt)
        self.assertIn("sample_stream_adapter", user_prompt)
        self.assertIn("rtl/axi_lite_write_ctrl.v", user_prompt)

    def test_system_his_v12_prompt_includes_rl_accelerator_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_rl_accelerator_shell",
            width=8,
            project_name="rl_accelerator_shell_8bit",
            description="Generate an integrated RL accelerator shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_rl_accelerator_shell", user_prompt)
        self.assertIn("host_config_bank", user_prompt)
        self.assertIn("sample_capture_stage", user_prompt)
        self.assertIn("policy_value_core", user_prompt)
        self.assertIn("td_update_core", user_prompt)
        self.assertIn("result_stream_stage", user_prompt)
        self.assertIn("rtl/result_stream_stage.v", user_prompt)

    def test_system_his_v12_prompt_includes_batch_rl_accelerator_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_batch_rl_accelerator_shell",
            width=8,
            project_name="batch_rl_accelerator_shell_8bit",
            description="Generate a two-lane batch RL accelerator shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_batch_rl_accelerator_shell", user_prompt)
        self.assertIn("batch_config_bank", user_prompt)
        self.assertIn("batch_sample_buffer", user_prompt)
        self.assertIn("dual_policy_value_core", user_prompt)
        self.assertIn("dual_td_update_core", user_prompt)
        self.assertIn("batch_result_stage", user_prompt)
        self.assertIn("rtl/batch_result_stage.v", user_prompt)

    def test_system_his_v12_prompt_includes_replay_arbiter_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_replay_arbiter_shell",
            width=8,
            project_name="replay_arbiter_shell_8bit",
            description="Generate a replay arbiter shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_replay_arbiter_shell", user_prompt)
        self.assertIn("host_transition_packetizer", user_prompt)
        self.assertIn("replay_index_allocator", user_prompt)
        self.assertIn("replay_request_arbiter", user_prompt)
        self.assertIn("replay_memory_bank", user_prompt)
        self.assertIn("sample_packet_stage", user_prompt)
        self.assertIn("rtl/replay_memory_bank.v", user_prompt)

    def test_system_his_v12_prompt_includes_alu_control_unit_guidance(self) -> None:
        request = ProjectRequest(
            task_type="alu_control_unit",
            width=8,
            project_name="alu_control_unit_8bit",
            description="Generate an ALU control unit.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for alu_control_unit", user_prompt)
        self.assertIn("control_decode", user_prompt)
        self.assertIn("alu_core", user_prompt)
        self.assertIn("status_flags", user_prompt)
        self.assertIn("top ports must include clk, rst_n, valid, ready, op, lhs, rhs", user_prompt)
        self.assertIn("rtl/status_flags.v", user_prompt)

    def test_system_his_v12_prompt_includes_crc_stream_checker_guidance(self) -> None:
        request = ProjectRequest(
            task_type="crc_stream_checker",
            width=8,
            project_name="crc_stream_checker_8bit",
            description="Generate a streaming CRC checker.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for crc_stream_checker", user_prompt)
        self.assertIn("stream_frame_accumulator", user_prompt)
        self.assertIn("crc8_update", user_prompt)
        self.assertIn("crc_status", user_prompt)
        self.assertIn("frame_start", user_prompt)
        self.assertIn("expected_crc", user_prompt)
        self.assertIn("rtl/crc8_update.v", user_prompt)

    def test_system_his_v12_initial_prompt_keeps_structured_control_guidance_brief(self) -> None:
        request = ProjectRequest(
            task_type="composed_stream_fork",
            width=8,
            project_name="fork_8bit",
            description="Generate a stream fork.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("fsm_transition rules must reference a declared state.fsms entry", user_prompt)
        self.assertNotIn("Do not leave fsm, from, to, effect.action, or effect.target empty", user_prompt)
        self.assertNotIn("If no FSM is needed, use handshake_rule, enable_rule, or stall_rule instead", user_prompt)

    def test_system_his_retry_feedback_includes_task_specific_fidelity_guidance(self) -> None:
        messages = [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Generate a System-HIS."},
        ]

        retry_messages = _with_system_his_retry_feedback(
            messages,
            "DeepSeek System-HIS REQ2HIS fidelity failed: missing top ports",
            '{"schema_version":"system-his-v1.2"}',
            task_type="composed_stream_accumulator",
        )
        retry_prompt = retry_messages[-1]["content"]

        self.assertIn("Required top ports: clk, rst_n, in_valid, in_data, in_ready, sample_valid, sum", retry_prompt)
        self.assertIn("input_buffer.out_valid to accumulator.sample_valid and top.sample_valid", retry_prompt)
        self.assertIn("Do not leave top.sample_valid declared but disconnected", retry_prompt)
        self.assertIn("accumulator_core.sample_valid must be an input port", retry_prompt)
        self.assertIn("Do not create sample_valid_in", retry_prompt)
        self.assertIn("Do not rename these ports to AXI-style names", retry_prompt)
        self.assertIn("s_axis_tvalid", retry_prompt)
        self.assertIn("Do not leave fsm, from, to, effect.action, or effect.target empty", retry_prompt)
        self.assertIn("If no FSM is needed, use handshake_rule, enable_rule, or stall_rule instead", retry_prompt)
        self.assertIn("top.resets[].polarity must be active_low or active_high", retry_prompt)
        self.assertIn("top.resets[].kind must be sync or async", retry_prompt)
        self.assertIn('Use {"name": "rst_n", "polarity": "active_low"', retry_prompt)
        self.assertIn("Every instances[].parameter_values key must be declared in that component's parameters", retry_prompt)
        self.assertIn("Every components[].source must be one of artifacts.rtl_sources", retry_prompt)
        self.assertIn('Do not use placeholder sources such as "library"', retry_prompt)
        self.assertIn("Every state.fsms[] entry must declare owner or use <instance>.<fsm> naming", retry_prompt)
        self.assertIn("FSM owner must be top or an instances[].name", retry_prompt)
        self.assertIn("State names across registers, counters, fsms, buffers, and memories must be globally unique", retry_prompt)

    def test_system_his_retry_feedback_interleaves_assistant_turn(self) -> None:
        messages = [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Generate a System-HIS."},
        ]

        retry_messages = _with_system_his_retry_feedback(
            messages,
            "bad json",
            '{"bad": true}',
            task_type="counter",
        )
        roles = [message["role"] for message in retry_messages]

        self.assertEqual(roles[-2:], ["assistant", "user"])
        self.assertNotEqual(roles[-2], roles[-1])

    def test_his_project_retry_feedback_interleaves_assistant_turn(self) -> None:
        messages = [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Generate behavior files."},
        ]

        retry_messages = _with_his_project_retry_feedback(messages, "bad json", '{"bad": true}')
        roles = [message["role"] for message in retry_messages]

        self.assertEqual(roles[-2:], ["assistant", "user"])
        self.assertNotEqual(roles[-2], roles[-1])

    def test_system_his_retry_feedback_includes_fsm_state_guidance_for_pipeline_tasks(self) -> None:
        messages = [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Generate a System-HIS."},
        ]

        vector_retry = _with_system_his_retry_feedback(
            messages,
            "DeepSeek System-HIS v1.2 failed validation: fsm states are empty",
            '{"schema_version":"system-his-v1.2"}',
            task_type="composed_vector_mac_pipeline",
        )[-1]["content"]
        td_retry = _with_system_his_retry_feedback(
            messages,
            "DeepSeek System-HIS v1.2 failed validation: fsm states are empty",
            '{"schema_version":"system-his-v1.2"}',
            task_type="composed_td_update_core",
        )[-1]["content"]

        self.assertIn("mac_core_fsm is declared", vector_retry)
        self.assertIn("states IDLE/ACCUMULATE/OUTPUT", vector_retry)
        self.assertIn("control_flow.effect must be an object", vector_retry)
        self.assertIn("out_fsm is declared", td_retry)
        self.assertIn("states IDLE/VALID", td_retry)
        self.assertIn("all fsm_transition rules must use fsm out_fsm", td_retry)

    def test_system_his_retry_feedback_rejects_join_accumulator_alias_ports(self) -> None:
        messages = [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Generate a System-HIS."},
        ]

        retry_prompt = _with_system_his_retry_feedback(
            messages,
            "REQ2HIS fidelity: component accumulator_core has unexpected port 'sample_valid_in'",
            '{"schema_version":"system-his-v1.2"}',
            task_type="composed_dual_stream_join",
        )[-1]["content"]

        self.assertIn("accumulator_core.sample_valid must remain a single input port", retry_prompt)
        self.assertIn("Do not create sample_valid_in, sample_valid_out, sample_ready_in, or sample_ready_out", retry_prompt)

    def test_system_his_retry_feedback_includes_crc_stream_checker_ports(self) -> None:
        messages = [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Generate a System-HIS."},
        ]

        retry_messages = _with_system_his_retry_feedback(
            messages,
            "DeepSeek System-HIS REQ2HIS fidelity failed: missing top ports",
            '{"schema_version":"system-his-v1.2"}',
            task_type="crc_stream_checker",
        )
        retry_prompt = retry_messages[-1]["content"]

        self.assertIn(
            "Required top ports: clk, rst_n, in_valid, in_data, frame_start, frame_end, expected_crc, out_ready, in_ready, out_valid, crc_value, crc_match",
            retry_prompt,
        )
        self.assertIn("Keep stream_frame_accumulator, crc8_update, and crc_status as separate RTL modules", retry_prompt)

    def test_deepseek_his_project_generator_merges_behavior_into_checked_skeleton(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeChatClient(json.dumps({"behavior_files": _behavior_files_for_system_his_v12(system_his)}))
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
        self.assertNotIn("BEHAVIOR_HOLE", project.files["rtl/stream_join.v"])
        self.assertIn("assign out_valid", project.files["rtl/stream_join.v"])
        self.assertEqual(client.call_count, 1)
        self.assertEqual(client.stream_call_count, 1)
        self.assertEqual(client.chat_call_count, 0)
        self.assertIn('"schema_version": "system-his-v1.2"', client.messages[1]["content"])
        self.assertIn("Do not change component, instance, top port, data_flow, or control_flow names", client.messages[1]["content"])

    def test_deepseek_his_project_generator_rejects_legacy_full_project_response(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeChatClient(json.dumps({"files": _project_files_for_system_his_v12(system_his)}))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with self.assertRaisesRegex(ValueError, "HIS2PROJECT response must contain behavior_files"):
            DeepSeekHisProjectGenerator(client, max_attempts=1).generate(request, platform, system_his)

    def test_deepseek_his_project_generator_rejects_behavior_for_structural_file(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeChatClient(json.dumps({"behavior_files": {"rtl/top.v": "module top; endmodule"}}))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with self.assertRaisesRegex(ValueError, "does not contain a BEHAVIOR_HOLE"):
            DeepSeekHisProjectGenerator(client, max_attempts=1).generate(request, platform, system_his)

    def test_deepseek_his_project_generator_rejects_complete_module_behavior(self) -> None:
        system_his = _system_his_v12_fixture()
        behavior_files = _behavior_files_for_system_his_v12(system_his)
        behavior_files["rtl/stream_join.v"] = "module stream_join; endmodule"
        client = FakeChatClient(json.dumps({"behavior_files": behavior_files}))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with self.assertRaisesRegex(ValueError, "must contain behavior body only"):
            DeepSeekHisProjectGenerator(client, max_attempts=1).generate(request, platform, system_his)

    def test_deepseek_his_project_generator_retries_with_feedback_after_complete_module_behavior(self) -> None:
        system_his = _system_his_v12_fixture()
        invalid_behavior_files = _behavior_files_for_system_his_v12(system_his)
        invalid_behavior_files["rtl/stream_join.v"] = "module stream_join; endmodule"
        valid_behavior_files = _behavior_files_for_system_his_v12(system_his)
        client = FakeChatClient(
            [
                json.dumps({"behavior_files": invalid_behavior_files}),
                json.dumps({"behavior_files": valid_behavior_files}),
            ]
        )
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = DeepSeekHisProjectGenerator(client, max_attempts=2).generate(request, platform, system_his)

        self.assertIn("rtl/stream_join.v", project.files)
        self.assertEqual(client.stream_call_count, 2)
        retry_prompt = client.messages_history[1][-1]["content"]
        self.assertIn("Your previous behavior_files output failed validation", retry_prompt)
        self.assertIn("must contain behavior body only", retry_prompt)
        self.assertIn("Drive every declared output", retry_prompt)
        self.assertIn("Every case statement must include a default branch", retry_prompt)
        self.assertIn("WIDTHEXPAND or WIDTHTRUNC", retry_prompt)
        self.assertIn("intentionally unused high/low bits", retry_prompt)
        self.assertIn("Avoid undriven signals, incomplete case coverage", retry_prompt)

    def test_deepseek_his_project_generator_rejects_reserved_identifier_behavior(self) -> None:
        system_his = _system_his_v12_fixture()
        behavior_files = _behavior_files_for_system_his_v12(system_his)
        behavior_files["rtl/skid_buffer.v"] = "reg [DATA_WIDTH-1:0] buf [0:1];"
        client = FakeChatClient(json.dumps({"behavior_files": behavior_files}))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with self.assertRaisesRegex(ValueError, "Verilog reserved keyword 'buf'"):
            DeepSeekHisProjectGenerator(client, max_attempts=1).generate(request, platform, system_his)

    def test_deepseek_his_project_generator_retries_after_reserved_identifier_behavior(self) -> None:
        system_his = _system_his_v12_fixture()
        invalid_behavior_files = _behavior_files_for_system_his_v12(system_his)
        invalid_behavior_files["rtl/skid_buffer.v"] = "reg [DATA_WIDTH-1:0] buf [0:1];"
        valid_behavior_files = _behavior_files_for_system_his_v12(system_his)
        client = FakeChatClient(
            [
                json.dumps({"behavior_files": invalid_behavior_files}),
                json.dumps({"behavior_files": valid_behavior_files}),
            ]
        )
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = DeepSeekHisProjectGenerator(client, max_attempts=2).generate(request, platform, system_his)

        self.assertNotIn("reg [DATA_WIDTH-1:0] buf", project.files["rtl/skid_buffer.v"])
        self.assertEqual(client.stream_call_count, 2)
        retry_prompt = client.messages_history[1][-1]["content"]
        self.assertIn("Verilog reserved keyword 'buf'", retry_prompt)

    def test_deepseek_his_project_generator_rejects_project_that_breaks_checked_contract(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeChatClient(json.dumps({"behavior_files": {"rtl/missing.v": "assign x = y;"}}))
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with self.assertRaisesRegex(ValueError, "is not part of the deterministic skeleton"):
            DeepSeekHisProjectGenerator(client, max_attempts=1).generate(request, platform, system_his)

    def test_his_project_prompt_requires_behavior_only_response(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        system_his = _system_his_v12_fixture()
        system_his["state"]["fsms"].append(
            {
                "name": "join_core.arb_fsm",
                "states": ["IDLE", "SEND_0", "SEND_1"],
                "initial": "IDLE",
                "reset_state": "IDLE",
            }
        )

        messages = _his_project_messages(request, platform, system_his)
        user_prompt = messages[1]["content"]

        self.assertIn("Generate behavior bodies for a contract-preserving SR2FPGA Verilog RTL skeleton", user_prompt)
        self.assertIn('"behavior_files"', user_prompt)
        self.assertIn("Do not return system_his.json, manifest.json, rtl/top.v", user_prompt)
        self.assertIn("Do not change component, instance, top port, data_flow, or control_flow names", user_prompt)
        self.assertIn("Generated behavior must be Verilator -Wall clean", user_prompt)
        self.assertIn("Make arithmetic widths explicit", user_prompt)
        self.assertIn("WIDTHEXPAND or WIDTHTRUNC", user_prompt)
        self.assertIn("UNUSEDSIGNAL on partial product bits", user_prompt)
        self.assertIn("include a default branch for every case statement", user_prompt)
        self.assertIn("Use declared FSM state localparams from the deterministic skeleton", user_prompt)
        self.assertIn("Do not rename, omit, or replace System-HIS state.fsms states", user_prompt)
        self.assertIn("IDLE", user_prompt)
        self.assertIn("SEND_0", user_prompt)
        self.assertIn('"rtl/stream_join.v"', user_prompt)
        self.assertNotIn('"files"', user_prompt)

    def test_deepseek_two_stage_project_generator_runs_req2his_then_his2project(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeChatClient(
            [
                json.dumps(system_his),
                json.dumps({"behavior_files": _behavior_files_for_system_his_v12(system_his)}),
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
        self.assertEqual(client.chat_call_count, 0)
        self.assertEqual(client.stream_call_count, 2)
        self.assertIn("Generate a canonical System-HIS v1.2", client.messages_history[0][1]["content"])
        self.assertIn(
            "Generate behavior bodies for a contract-preserving SR2FPGA Verilog RTL skeleton",
            client.messages_history[1][1]["content"],
        )

    def test_deepseek_oracle_his_project_generator_skips_req2his_and_runs_his2project(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        oracle_his = _deterministic_system_his(request)
        behavior_files = _behavior_files_for_contract_skeleton(request, platform, oracle_his)
        client = FakeChatClient(json.dumps({"behavior_files": behavior_files}))
        events = []

        project = DeepSeekOracleHisProjectGenerator(client, event_sink=events.append).generate(request, platform)

        self.assertEqual(project.project_name, "join_8bit")
        self.assertIn("rtl/stream_join.v", project.files)
        self.assertEqual(client.call_count, 1)
        self.assertEqual(client.chat_call_count, 0)
        self.assertEqual(client.stream_call_count, 1)
        self.assertIn("Generate behavior bodies for a contract-preserving SR2FPGA Verilog RTL skeleton", client.messages[1]["content"])
        self.assertIn('"schema_version": "system-his-v1.2"', client.messages[1]["content"])
        self.assertIn("Make arithmetic widths explicit", client.messages[1]["content"])
        self.assertEqual([event["stage"] for event in events], ["oracle_req2his", "oracle_req2his", "his2project", "his2project"])

    def test_deepseek_two_stage_project_generator_emits_stage_events(self) -> None:
        system_his = _system_his_v12_fixture()
        client = FakeChatClient(
            [
                json.dumps(system_his),
                json.dumps({"behavior_files": _behavior_files_for_system_his_v12(system_his)}),
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

    def test_deepseek_two_stage_project_generator_emits_req2his_retry_events(self) -> None:
        invalid = _system_his_v12_fixture()
        invalid["instances"][0]["component"] = "missing_component"
        system_his = _system_his_v12_fixture()
        client = FakeChatClient(
            [
                json.dumps(invalid),
                json.dumps(system_his),
                json.dumps({"behavior_files": _behavior_files_for_system_his_v12(system_his)}),
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

        retry_events = [event for event in events if event["event"] == "generation_stage_retry"]
        self.assertEqual(len(retry_events), 1)
        self.assertEqual(retry_events[0]["stage"], "req2his")
        self.assertEqual(retry_events[0]["attempt_id"], 0)
        self.assertIn("missing component 'missing_component'", retry_events[0]["error"])

    def test_deepseek_project_generator_retries_after_invalid_response(self) -> None:
        client = FakeChatClient(
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
        client = FakeChatClient([single_file_payload, multi_file_payload])
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
        client = FakeChatClient(repaired_payload)
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
        client = FakeChatClient(repaired_payload)
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
        self.assertIn("Repair quality rules", prompt)
        self.assertIn("Do not introduce a new syntax error", prompt)
        self.assertIn("WIDTHEXPAND, WIDTHTRUNC, UNUSEDSIGNAL", prompt)
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

    def test_repair_prompt_preserves_v12_system_his_schema(self) -> None:
        system_his = _system_his_v12_fixture()
        project = GeneratedProject(
            project_name="join_8bit",
            files={
                **_project_files_for_system_his_v12(system_his),
                "rtl/top.v": "module top; endmodule\n",
            },
        )
        diagnosis = {"stage": "lint", "failure_type": "syntax_error", "root_cause": "syntax error"}

        messages = _repair_messages(project, diagnosis)
        prompt = messages[1]["content"]

        self.assertIn("system-his-v1.2", prompt)
        self.assertIn("Preserve the existing canonical System-HIS v1.2 contract", prompt)
        self.assertNotIn("system-his-v1.1 structure-contract schema", prompt)

    def test_deepseek_repairer_rejects_v12_schema_downgrade(self) -> None:
        system_his = _system_his_v12_fixture()
        downgraded_his = {"schema_version": "system-his-v1.1", "project_name": "join_8bit"}
        original = GeneratedProject(project_name="join_8bit", files=_project_files_for_system_his_v12(system_his))
        repaired_files = {
            **_project_files_for_system_his_v12(system_his),
            "system_his.json": json.dumps(downgraded_his) + "\n",
        }
        client = FakeChatClient(json.dumps({"files": repaired_files}))
        diagnosis = {"stage": "lint", "failure_type": "syntax_error", "root_cause": "syntax error"}

        with self.assertRaisesRegex(ValueError, "DeepSeek repair system_his.json failed validation"):
            DeepSeekRepairer(client, max_attempts=1).repair(original, diagnosis)

    def test_deepseek_repairer_rejects_unrelated_v12_contract_mutation(self) -> None:
        system_his = _system_his_v12_fixture()
        mutated_his = json.loads(json.dumps(system_his))
        mutated_his["components"][0]["intent"] = "silently rewritten architecture intent"
        original = GeneratedProject(project_name="join_8bit", files=_project_files_for_system_his_v12(system_his))
        repaired_files = {
            **_project_files_for_system_his_v12(system_his),
            "system_his.json": json.dumps(mutated_his, indent=2) + "\n",
            "rtl/top.v": "module top; endmodule\n",
        }
        client = FakeChatClient(json.dumps({"files": repaired_files}))
        diagnosis = {"stage": "lint", "failure_type": "syntax_error", "root_cause": "rtl/top.v syntax error"}

        with self.assertRaisesRegex(ValueError, "System-HIS v1.2 contract changed during RTL repair"):
            DeepSeekRepairer(client, max_attempts=1).repair(original, diagnosis)

    def test_deepseek_repairer_rejects_lint_fix_that_breaks_v12_l0_contract(self) -> None:
        original = ProjectGenerator().generate(
            ProjectRequest(task_type="composed_dual_stream_join", width=8, project_name="join_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        repaired_files = dict(original.files)
        repaired_files["rtl/stream_join.v"] = repaired_files["rtl/stream_join.v"].replace(
            "    input wire in1_valid,\n"
            "    output wire in1_ready,\n"
            "    input wire [WIDTH-1:0] in1_data,\n",
            "",
        )
        self.assertNotEqual(repaired_files["rtl/stream_join.v"], original.files["rtl/stream_join.v"])
        client = FakeChatClient(json.dumps({"files": repaired_files}))
        diagnosis = {
            "stage": "lint",
            "failure_type": "lint_warning_as_error",
            "root_cause": "%Warning-UNUSEDSIGNAL: rtl/stream_join.v: Signal is not used: 'in1_data'",
            "affected_files": [],
        }

        with self.assertRaisesRegex(ValueError, "repair introduced L0 contract violations"):
            DeepSeekRepairer(client, max_attempts=1).repair(original, diagnosis)

    def test_project_prompt_requests_agent_manifest_schema(self) -> None:
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        messages = _project_messages(request, platform)
        user_prompt = messages[1]["content"]

        self.assertIn('"top_module": "top"', user_prompt)
        self.assertIn('"sources": ["rtl/top.v"]', user_prompt)
        self.assertIn('"constraints": {"timing": "constraints/timing.sdc"}', user_prompt)
        self.assertIn('"simulation": {"testbench": "sim/tb_top.v"}', user_prompt)

    def test_project_prompt_requires_icarus_portable_testbench_arrays(self) -> None:
        request = ProjectRequest(task_type="composed_dual_stream_join", width=8, project_name="join_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        prompt = _project_messages(request, platform)[1]["content"]

        self.assertIn("Icarus Verilog", prompt)
        self.assertIn("Do not initialize unpacked arrays with aggregate literals", prompt)
        self.assertIn("initial block assignments", prompt)
        self.assertIn("Every wait loop must be bounded", prompt)
        self.assertIn("TEST_FAIL on timeout", prompt)
        self.assertIn("Drive and withdraw valid-ready stimulus away from the DUT sampling edge", prompt)
        self.assertIn("Observe outputs after nonblocking assignments have settled", prompt)
        self.assertIn("After wait(out_valid), check the current transaction before advancing", prompt)
        self.assertIn("Do not hold input valid high until out_valid", prompt)
        self.assertIn("deassert or advance each input valid after its own input ready handshake", prompt)
        self.assertIn("Exercise back-to-back valid-ready transfers", prompt)
        self.assertIn("check each output transaction", prompt)

    def test_his_project_prompt_requires_icarus_portable_testbench_arrays(self) -> None:
        request = ProjectRequest(task_type="composed_dual_stream_join", width=8, project_name="join_8bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        system_his = _system_his_v12_fixture()

        prompt = _his_project_messages(request, platform, system_his)[1]["content"]

        self.assertIn("Icarus Verilog", prompt)
        self.assertIn("Do not initialize unpacked arrays with aggregate literals", prompt)
        self.assertIn("initial block assignments", prompt)
        self.assertIn("Every wait loop must be bounded", prompt)
        self.assertIn("TEST_FAIL on timeout", prompt)
        self.assertIn("Drive and withdraw valid-ready stimulus away from the DUT sampling edge", prompt)
        self.assertIn("Observe outputs after nonblocking assignments have settled", prompt)
        self.assertIn("After wait(out_valid), check the current transaction before advancing", prompt)
        self.assertIn("Do not hold input valid high until out_valid", prompt)
        self.assertIn("deassert or advance each input valid after its own input ready handshake", prompt)
        self.assertIn("Exercise back-to-back valid-ready transfers", prompt)
        self.assertIn("check each output transaction", prompt)

    def test_repair_prompt_requires_icarus_portable_testbench_arrays(self) -> None:
        system_his = _system_his_v12_fixture()
        project = GeneratedProject(project_name="join_8bit", files=_project_files_for_system_his_v12(system_his))
        diagnosis = {
            "stage": "sim_compile",
            "failure_type": "testbench_simulator_compatibility",
            "root_cause": "Icarus cannot elaborate unpacked array aggregate initialization",
            "affected_files": ["sim/tb_top.v"],
        }

        prompt = _repair_messages(project, diagnosis)[1]["content"]

        self.assertIn("Icarus Verilog", prompt)
        self.assertIn("Do not initialize unpacked arrays with aggregate literals", prompt)
        self.assertIn("initial block assignments", prompt)
        self.assertIn("Every wait loop must be bounded", prompt)
        self.assertIn("TEST_FAIL on timeout", prompt)
        self.assertIn("Drive and withdraw valid-ready stimulus away from the DUT sampling edge", prompt)
        self.assertIn("Observe outputs after nonblocking assignments have settled", prompt)
        self.assertIn("After wait(out_valid), check the current transaction before advancing", prompt)
        self.assertIn("Do not hold input valid high until out_valid", prompt)
        self.assertIn("deassert or advance each input valid after its own input ready handshake", prompt)
        self.assertIn("Exercise back-to-back valid-ready transfers", prompt)
        self.assertIn("check each output transaction", prompt)

    def test_repair_prompt_keeps_unused_parameter_fixes_interface_consistent(self) -> None:
        system_his = _system_his_v12_fixture()
        project = GeneratedProject(project_name="join_8bit", files=_project_files_for_system_his_v12(system_his))
        diagnosis = {
            "stage": "lint",
            "failure_type": "lint_warning_as_error",
            "root_cause": "%Warning-UNUSEDPARAM: rtl/skid_buffer.v:1:56: Parameter is not used: 'DEPTH'",
            "affected_files": ["rtl/skid_buffer.v", "rtl/top.v"],
        }

        prompt = _repair_messages(project, diagnosis)[1]["content"]

        self.assertIn("Unused parameter repair rules", prompt)
        self.assertIn("module declaration and every instantiation must agree", prompt)
        self.assertIn("remove the parameter override from all instantiations", prompt)

    def test_repair_prompt_does_not_let_functional_mismatch_cheat_by_changing_expected_values(self) -> None:
        system_his = _system_his_v12_fixture()
        project = GeneratedProject(project_name="join_8bit", files=_project_files_for_system_his_v12(system_his))
        diagnosis = {
            "stage": "sim_run",
            "failure_type": "functional_mismatch",
            "root_cause": "TEST_FAIL: mismatch at 1, expected 12, got 10",
            "affected_files": ["rtl/top.v", "sim/tb_top.v"],
        }

        prompt = _repair_messages(project, diagnosis)[1]["content"]

        self.assertIn("Do not make the testbench pass by changing expected values", prompt)
        self.assertIn("prefer fixing RTL behavior", prompt)
        self.assertIn("lost or duplicated valid-ready transfer", prompt)
        self.assertIn("Only change expected values when the diagnosis explicitly says the testbench expectation is wrong", prompt)

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
            mock.patch.object(cli, "build_project_generator", return_value="fake-llm-generator") as build_generator,
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
        self.assertEqual(build_generator.call_args.kwargs["model"], "deepseek-v4-pro")
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


class FakeChatClient:
    def __init__(self, content) -> None:
        self.content = content
        self.call_count = 0
        self.chat_call_count = 0
        self.stream_call_count = 0
        self.messages = []
        self.messages_history = []

    def chat(self, messages):
        self.chat_call_count += 1
        return self._respond(messages)

    def stream_chat(self, messages):
        self.stream_call_count += 1
        return self._respond(messages)

    def _respond(self, messages):
        self.call_count += 1
        self.messages = messages
        self.messages_history.append(messages)
        if isinstance(self.content, list):
            return self.content[self.call_count - 1]
        return self.content


class FakeHTTPResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            chunk = self.body[self.offset :]
            self.offset = len(self.body)
            return chunk
        chunk = self.body[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk

    def close(self) -> None:
        pass


class FakeStreamingHTTPResponse:
    def __init__(self, lines: list[bytes]) -> None:
        self.lines = list(lines)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def readline(self) -> bytes:
        if not self.lines:
            return b""
        return self.lines.pop(0)


class FakeNeverEndingHTTPResponse(FakeHTTPResponse):
    def __init__(self, body_for_unbounded_read: bytes) -> None:
        super().__init__(body_for_unbounded_read)

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            return self.body
        return b" "


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


def _deterministic_system_his(request: ProjectRequest) -> dict[str, object]:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    project = ProjectGenerator().generate(request, platform)
    return json.loads(project.files["system_his.json"])


def _project_files_for_system_his_v12(system_his: dict[str, object]) -> dict[str, str]:
    request = ProjectRequest(
        task_type="composed_dual_stream_join",
        width=8,
        project_name="join_8bit",
        description="Generate a dual-stream join and accumulator project.",
    )
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    return build_contract_skeleton_project(request, platform, system_his).files


def _behavior_files_for_system_his_v12(system_his: dict[str, object]) -> dict[str, str]:
    files: dict[str, str] = {}
    for component in system_his["components"]:
        source = str(component["source"])
        if source == "rtl/stream_join.v":
            files[source] = "assign out_valid = in0_valid && in1_valid;\nassign out_data = in0_data + in1_data;"
        else:
            files[source] = "// behavior intentionally omitted in unit-test fixture"
    return files


def _behavior_files_for_contract_skeleton(
    request: ProjectRequest,
    platform: PlatformProfile,
    system_his: dict[str, object],
) -> dict[str, str]:
    behavior_files = _behavior_files_for_system_his_v12(system_his)
    skeleton = build_contract_skeleton_project(request, platform, system_his)
    return {
        path: body
        for path, body in behavior_files.items()
        if path in skeleton.files and "BEHAVIOR_HOLE" in skeleton.files[path]
    }


if __name__ == "__main__":
    unittest.main()
