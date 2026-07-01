import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent import PlatformProfile, ProjectGenerator, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import COMPONENT_TOPOLOGIES
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0
from LLM.src.sr2fpga_agent.testbench_checker import check_testbench_static_issues


class ProjectGeneratorTest(unittest.TestCase):
    def test_generates_minimal_counter_project_package(self) -> None:
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(
            name="generic_verilog",
            vendor="generic",
            toolchain="open_source",
            clock_hz=100_000_000,
        )

        project = ProjectGenerator().generate(request, platform)

        expected_paths = {
            "system_his.json",
            "manifest.json",
            "rtl/top.v",
            "constraints/timing.sdc",
            "sim/tb_top.v",
            "reports/predicted_qor.json",
        }
        self.assertEqual(set(project.files), expected_paths)

        manifest = json.loads(project.files["manifest.json"])
        self.assertEqual(manifest["project_name"], "counter_8bit")
        self.assertEqual(manifest["top_module"], "top")
        self.assertEqual(manifest["sources"], ["rtl/top.v"])
        self.assertEqual(manifest["simulation"]["testbench"], "sim/tb_top.v")

        rtl = project.files["rtl/top.v"]
        self.assertRegex(rtl, r"module\s+top\s*\(")
        self.assertIn("input wire clk", rtl)
        self.assertIn("input wire rst_n", rtl)
        self.assertIn("input wire en", rtl)
        self.assertIn("output reg [7:0] count", rtl)

        testbench = project.files["sim/tb_top.v"]
        self.assertRegex(testbench, r"top\s+dut\s*\(")
        self.assertIn(".count(count)", testbench)
        self.assertIn("TEST_PASS", testbench)

        predicted_qor = json.loads(project.files["reports/predicted_qor.json"])
        self.assertEqual(predicted_qor["project_name"], "counter_8bit")
        self.assertEqual(predicted_qor["assumptions"]["counter_width"], 8)
        for key in ("lut", "ff", "bram", "dsp", "fmax_mhz", "confidence"):
            self.assertIn(key, predicted_qor["predicted"])

    def test_manifest_top_module_matches_rtl_module_name(self) -> None:
        request = ProjectRequest(task_type="counter", width=4, project_name="counter_4bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = ProjectGenerator().generate(request, platform)

        manifest = json.loads(project.files["manifest.json"])
        rtl = project.files["rtl/top.v"]
        module_name = re.search(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_$]*)\s*\(", rtl)
        self.assertIsNotNone(module_name)
        self.assertEqual(manifest["top_module"], module_name.group(1))

    def test_generates_fifo_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="fifo", width=8, project_name="fifo_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertEqual(_task_type(project), "fifo")
        self.assertIn("module top", project.files["rtl/top.v"])
        self.assertIn("wr_en", project.files["rtl/top.v"])
        self.assertIn("rd_en", project.files["rtl/top.v"])
        self.assertIn("full", project.files["rtl/top.v"])
        self.assertIn("empty", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_simple_fsm_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="simple_fsm", width=4, project_name="fsm_sequence_4bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertEqual(_task_type(project), "simple_fsm")
        self.assertIn("state", project.files["rtl/top.v"])
        self.assertIn("start", project.files["rtl/top.v"])
        self.assertIn("done", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_ram_read_write_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="ram_read_write", width=16, project_name="ram_rw_16bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertEqual(_task_type(project), "ram_read_write")
        self.assertIn("addr", project.files["rtl/top.v"])
        self.assertIn("wdata", project.files["rtl/top.v"])
        self.assertIn("rdata", project.files["rtl/top.v"])
        self.assertIn("mem", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_single_module_families_emit_valid_system_his_v12(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("counter", 8, "counter_8bit"),
            ("fifo", 8, "fifo_8bit"),
            ("simple_fsm", 4, "fsm_sequence_4bit"),
            ("ram_read_write", 16, "ram_rw_16bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                system_his = _system_his(project)

                self.assertEqual(system_his["schema_version"], "system-his-v1.2")
                self.assertTrue(check_project_l0(project).passed, check_project_l0(project).errors)

    def test_multimodule_families_emit_valid_system_his_v12(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("uart_tx", 8, "uart_tx_8bit"),
            ("spi_master", 8, "spi_master_8bit"),
            ("pwm_controller", 8, "pwm_controller_8bit"),
            ("fir_filter", 8, "fir_filter_8bit"),
            ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
            ("matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
            ("alu_control_unit", 8, "alu_control_unit_8bit"),
            ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
            ("composed_event_counter", 8, "composed_event_counter_8bit"),
            ("composed_stream_accumulator", 8, "composed_stream_accumulator_8bit"),
            ("composed_stream_fork", 8, "composed_stream_fork_8bit"),
            ("composed_dual_stream_join", 8, "composed_dual_stream_join_8bit"),
            ("composed_td_update_core", 8, "composed_td_update_core_8bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                system_his = _system_his(project)

                self.assertEqual(system_his["schema_version"], "system-his-v1.2")
                self.assertTrue(check_project_l0(project).passed, check_project_l0(project).errors)

    def test_streaming_multimodule_v12_records_timing_and_handshake_control(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
            ("composed_stream_accumulator", 8, "composed_stream_accumulator_8bit"),
            ("composed_stream_fork", 8, "composed_stream_fork_8bit"),
            ("composed_dual_stream_join", 8, "composed_dual_stream_join_8bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                system_his = _system_his(project)

                self.assertTrue(any("timing" in flow for flow in system_his["data_flow"]))
                self.assertIn("handshake_rule", {rule["kind"] for rule in system_his["control_flow"]})
                self.assertIn("stall_rule", {rule["kind"] for rule in system_his["control_flow"]})
                for flow in system_his["data_flow"]:
                    self.assertTrue(flow["path"][0].startswith("top."), flow)
                    self.assertTrue(flow["path"][-1].startswith("top."), flow)

    def test_generates_uart_tx_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "uart_tx",
            {"rtl/top.v", "rtl/uart_tx_core.v", "rtl/baud_tick_gen.v"},
            ["uart_tx_core", "baud_tick_gen", ".tx(tx)", ".busy(busy)"],
        )
        self.assertIn("output wire tx", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_pwm_controller_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="pwm_controller", width=8, project_name="pwm_controller_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "pwm_controller",
            {"rtl/top.v", "rtl/pwm_timer.v", "rtl/pwm_channel.v"},
            ["pwm_timer", "pwm_channel", ".pwm_out(pwm_out)"],
        )
        self.assertIn("input wire [7:0] duty", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_streaming_valid_ready_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="streaming_valid_ready",
                width=8,
                project_name="streaming_valid_ready_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "streaming_valid_ready",
            {"rtl/top.v", "rtl/stream_stage.v", "rtl/skid_buffer.v"},
            ["stream_stage", "skid_buffer", ".in_valid(in_valid)", ".out_ready(out_ready)"],
        )
        self.assertIn("out_valid", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_spi_master_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="spi_master", width=8, project_name="spi_master_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "spi_master",
            {"rtl/top.v", "rtl/spi_master_core.v", "rtl/clock_divider.v"},
            ["spi_master_core", "clock_divider", ".mosi(mosi)", ".miso(miso)", ".cs_n(cs_n)"],
        )
        self.assertIn("output wire sclk", project.files["rtl/top.v"])
        self.assertIn("sclk_edge_count", project.files["sim/tb_top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_fir_filter_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="fir_filter", width=8, project_name="fir_filter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "fir_filter",
            {"rtl/top.v", "rtl/fir_filter_core.v", "rtl/mac_unit.v"},
            ["fir_filter_core", "mac_unit", ".sample_valid(sample_valid)", ".result_valid(result_valid)"],
        )
        self.assertIn("result", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_matrix_vector_mac_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="matrix_vector_mac", width=8, project_name="matrix_vector_mac_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "matrix_vector_mac",
            {"rtl/top.v", "rtl/dot_product_engine.v", "rtl/mac_unit.v", "rtl/vector_rom.v"},
            ["dot_product_engine", "mac_unit", "vector_rom", ".done(done)"],
        )
        self.assertIn("result", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_alu_control_unit_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="alu_control_unit", width=8, project_name="alu_control_unit_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "alu_control_unit",
            {"rtl/top.v", "rtl/alu_core.v", "rtl/control_decode.v", "rtl/status_flags.v"},
            ["alu_core", "control_decode", "status_flags", ".result(result)", ".zero(zero)", ".carry(carry)"],
        )
        self.assertIn("input wire [2:0] op", project.files["rtl/top.v"])
        self.assertIn("output wire negative", project.files["rtl/top.v"])
        self.assertIn("expect_result(3'b000", project.files["sim/tb_top.v"])
        self.assertIn("expect_result(3'b111", project.files["sim/tb_top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_crc_stream_checker_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="crc_stream_checker", width=8, project_name="crc_stream_checker_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "crc_stream_checker",
            {"rtl/top.v", "rtl/crc8_update.v", "rtl/stream_frame_accumulator.v", "rtl/crc_status.v"},
            [
                "crc8_update",
                "stream_frame_accumulator",
                "crc_status",
                ".crc_value(crc_value)",
                ".crc_match(crc_match)",
            ],
        )
        self.assertIn("input wire frame_start", project.files["rtl/top.v"])
        self.assertIn("input wire frame_end", project.files["rtl/top.v"])
        self.assertIn("input wire out_ready", project.files["rtl/top.v"])
        self.assertIn("send_byte(8'h12", project.files["sim/tb_top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_composed_stream_accumulator_from_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_stream_accumulator",
                width=8,
                project_name="composed_stream_accumulator_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_stream_accumulator",
            {"rtl/top.v", "rtl/skid_buffer.v", "rtl/accumulator_core.v"},
            ["skid_buffer", "accumulator_core", ".sample_valid(sample_valid)", ".sum(sum)"],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t2_stream_accumulator")
        self.assertEqual(architecture["difficulty_tier"], "T1")
        self.assertEqual(architecture["component_library"], "sr2fpga_deterministic_components_v1")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["skid_buffer", "accumulator_core"],
        )
        self.assertIn(
            {"from": "skid_buffer.out_data", "to": "accumulator_core.sample"},
            architecture["topology"]["edges"],
        )
        self.assertGreaterEqual(len(system_his["connections"]), 8)

    def test_generates_composed_event_counter_from_t1_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_event_counter",
                width=8,
                project_name="composed_event_counter_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_event_counter",
            {"rtl/top.v", "rtl/event_gate.v", "rtl/counter_core.v"},
            ["event_gate", "counter_core", ".event_valid(event_valid)", ".count(count)"],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t1_event_counter")
        self.assertEqual(architecture["difficulty_tier"], "T1")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["event_gate", "counter_core"],
        )
        self.assertIn({"from": "event_gate.count_en", "to": "counter_core.en"}, architecture["topology"]["edges"])
        self.assertGreaterEqual(len(system_his["connections"]), 5)

    def test_generates_composed_stream_fork_from_t3_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_stream_fork",
                width=8,
                project_name="composed_stream_fork_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_stream_fork",
            {"rtl/top.v", "rtl/skid_buffer.v", "rtl/stream_fork.v", "rtl/stream_stage.v"},
            ["skid_buffer", "stream_fork", "stream_stage", ".out_valid(out0_valid)", ".out_valid(out1_valid)"],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t3_stream_fork")
        self.assertEqual(architecture["difficulty_tier"], "T2")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["skid_buffer", "stream_fork", "stream_stage"],
        )
        self.assertIn(
            {"from": "stream_fork.out1_data", "to": "stream_stage.in_data"},
            architecture["topology"]["edges"],
        )
        self.assertGreaterEqual(len(system_his["connections"]), 18)

    def test_generates_composed_dual_stream_join_from_t4_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_dual_stream_join",
                width=8,
                project_name="composed_dual_stream_join_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_dual_stream_join",
            {
                "rtl/top.v",
                "rtl/skid_buffer.v",
                "rtl/stream_join.v",
                "rtl/accumulator_core.v",
                "rtl/stream_stage.v",
            },
            ["skid_buffer", "stream_join", "accumulator_core", "stream_stage", ".out_valid(out_valid)"],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t4_dual_stream_join")
        self.assertEqual(architecture["difficulty_tier"], "T2")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["skid_buffer", "skid_buffer", "stream_join", "accumulator_core", "stream_stage"],
        )
        self.assertIn(
            {"from": "stream_join.out_data", "to": "accumulator_core.sample"},
            architecture["topology"]["edges"],
        )
        self.assertGreaterEqual(len(system_his["connections"]), 24)

    def test_generates_composed_vector_mac_pipeline_from_t5_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_vector_mac_pipeline",
                width=8,
                project_name="composed_vector_mac_pipeline_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_vector_mac_pipeline",
            {
                "rtl/top.v",
                "rtl/skid_buffer.v",
                "rtl/vector_mac_core.v",
                "rtl/stream_stage.v",
            },
            [
                "skid_buffer",
                "vector_mac_core",
                "stream_stage",
                ".in_valid(feature_valid)",
                ".in_valid(weight_valid)",
                ".feature_valid(feature_buf_valid)",
                ".weight_valid(weight_buf_valid)",
                ".out_valid(score_valid)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t5_vector_mac_pipeline")
        self.assertEqual(architecture["difficulty_tier"], "T3")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["skid_buffer", "skid_buffer", "vector_mac_core", "stream_stage"],
        )
        self.assertIn(
            {"from": "vector_mac_core.score_data", "to": "stream_stage.in_data"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire [7:0] feature_data", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] weight_data", project.files["rtl/top.v"])
        self.assertIn("input wire [15:0] bias", project.files["rtl/top.v"])
        self.assertIn("output wire [15:0] score_data", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 18)

    def test_generates_composed_td_update_core_from_t6_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_td_update_core",
                width=8,
                project_name="composed_td_update_core_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_td_update_core",
            {
                "rtl/top.v",
                "rtl/td_input_stage.v",
                "rtl/discount_core.v",
                "rtl/td_update_core.v",
                "rtl/stream_stage.v",
            },
            [
                "td_input_stage",
                "discount_core",
                "td_update_core",
                "stream_stage",
                ".reward(reward)",
                ".next_value(next_value)",
                ".td_error(update_td_error)",
                ".updated_value(update_value)",
                ".td_error_out(td_error)",
                ".updated_value_out(updated_value)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t6_td_update_core")
        self.assertEqual(architecture["difficulty_tier"], "T3")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["td_input_stage", "discount_core", "td_update_core", "stream_stage"],
        )
        self.assertIn(
            {"from": "discount_core.discounted_return", "to": "td_update_core.discounted_return"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire signed [7:0] reward", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] gamma", project.files["rtl/top.v"])
        self.assertIn("output wire signed [7:0] td_error", project.files["rtl/top.v"])
        self.assertIn("output wire signed [7:0] updated_value", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 18)
        data_flow_paths = [flow["path"] for flow in system_his["data_flow"]]
        self.assertIn(["top.reward", "u_td_input_stage.reward"], data_flow_paths)
        self.assertIn(["top.value", "u_td_input_stage.value"], data_flow_paths)
        self.assertIn(["top.next_value", "u_td_input_stage.next_value"], data_flow_paths)
        self.assertIn(["top.gamma", "u_td_input_stage.gamma"], data_flow_paths)
        self.assertIn(["top.alpha", "u_td_input_stage.alpha"], data_flow_paths)
        self.assertIn(["u_stream_stage.updated_value_out", "top.updated_value"], data_flow_paths)

    def test_generates_composed_policy_value_shell_from_t7_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_policy_value_shell",
                width=8,
                project_name="composed_policy_value_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_policy_value_shell",
            {
                "rtl/top.v",
                "rtl/config_reg_bank.v",
                "rtl/observation_stage.v",
                "rtl/policy_score_core.v",
                "rtl/action_select_core.v",
                "rtl/stream_stage.v",
            },
            [
                "config_reg_bank",
                "observation_stage",
                "policy_score_core",
                "action_select_core",
                "stream_stage",
                ".cfg_valid(cfg_valid)",
                ".obs0(obs0)",
                ".score1(policy_score1)",
                ".selected_action(select_action)",
                ".value_estimate(select_value)",
                ".selected_action_out(selected_action)",
                ".value_estimate_out(value_estimate)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t7_policy_value_shell")
        self.assertEqual(architecture["difficulty_tier"], "T3")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["config_reg_bank", "observation_stage", "policy_score_core", "action_select_core", "stream_stage"],
        )
        self.assertIn(
            {"from": "policy_score_core.score1", "to": "action_select_core.score1"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire cfg_valid", project.files["rtl/top.v"])
        self.assertIn("input wire [2:0] cfg_addr", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] cfg_data", project.files["rtl/top.v"])
        self.assertIn("input wire obs_valid", project.files["rtl/top.v"])
        self.assertIn("output wire action_valid", project.files["rtl/top.v"])
        self.assertIn("output wire selected_action", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] value_estimate", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 24)

    def test_generates_composed_replay_sample_shell_from_t8_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_replay_sample_shell",
                width=8,
                project_name="composed_replay_sample_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_replay_sample_shell",
            {
                "rtl/top.v",
                "rtl/host_sample_stage.v",
                "rtl/replay_store.v",
                "rtl/sample_pack_core.v",
                "rtl/sample_read_stage.v",
                "rtl/occupancy_counter.v",
            },
            [
                "host_sample_stage",
                "replay_store",
                "sample_pack_core",
                "sample_read_stage",
                "occupancy_counter",
                ".in_valid(host_valid)",
                ".write_valid(host_stage_valid)",
                ".read_valid(store_read_valid)",
                ".sample_state(sample_pack_state)",
                ".sample_state_out(sample_state)",
                ".occupancy_out(occupancy)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t8_replay_sample_shell")
        self.assertEqual(architecture["difficulty_tier"], "T3")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["host_sample_stage", "replay_store", "sample_pack_core", "sample_read_stage", "occupancy_counter"],
        )
        self.assertIn(
            {"from": "replay_store.read_valid", "to": "sample_read_stage.in_valid"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire host_valid", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] host_state", project.files["rtl/top.v"])
        self.assertIn("input wire host_action", project.files["rtl/top.v"])
        self.assertIn("output wire sample_valid", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] sample_next_state", project.files["rtl/top.v"])
        self.assertIn("output wire [2:0] occupancy", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 28)

    def test_generates_composed_host_protocol_shell_from_t9_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_host_protocol_shell",
                width=8,
                project_name="composed_host_protocol_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_host_protocol_shell",
            {
                "rtl/top.v",
                "rtl/axi_lite_write_ctrl.v",
                "rtl/axi_lite_read_ctrl.v",
                "rtl/control_reg_bank.v",
                "rtl/sample_stream_adapter.v",
                "rtl/irq_status.v",
            },
            [
                "axi_lite_write_ctrl",
                "axi_lite_read_ctrl",
                "control_reg_bank",
                "sample_stream_adapter",
                "irq_status",
                ".awvalid(s_axi_awvalid)",
                ".write_valid(write_valid)",
                ".read_valid(read_valid)",
                ".tdata(m_axis_tdata)",
                ".irq_out(irq)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t9_host_protocol_shell")
        self.assertEqual(architecture["difficulty_tier"], "T4")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["axi_lite_write_ctrl", "axi_lite_read_ctrl", "control_reg_bank", "sample_stream_adapter", "irq_status"],
        )
        self.assertIn(
            {"from": "sample_stream_adapter.tvalid", "to": "top.m_axis_tvalid"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire s_axi_awvalid", project.files["rtl/top.v"])
        self.assertIn("input wire [3:0] s_axi_awaddr", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] s_axi_wdata", project.files["rtl/top.v"])
        self.assertIn("output wire s_axi_rvalid", project.files["rtl/top.v"])
        self.assertIn("output wire [15:0] m_axis_tdata", project.files["rtl/top.v"])
        self.assertIn("output wire irq", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 30)

    def test_generates_composed_rl_accelerator_shell_from_t10_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_rl_accelerator_shell",
                width=8,
                project_name="composed_rl_accelerator_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_rl_accelerator_shell",
            {
                "rtl/top.v",
                "rtl/host_config_bank.v",
                "rtl/sample_capture_stage.v",
                "rtl/policy_value_core.v",
                "rtl/td_update_core.v",
                "rtl/result_stream_stage.v",
            },
            [
                "host_config_bank",
                "sample_capture_stage",
                "policy_value_core",
                "td_update_core",
                "result_stream_stage",
                ".cfg_valid(cfg_valid)",
                ".in_valid(sample_valid)",
                ".result_valid(result_valid)",
                ".updated_value_out(updated_value)",
                ".irq(irq)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t10_rl_accelerator_shell")
        self.assertEqual(architecture["difficulty_tier"], "T4")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            [
                "host_config_bank",
                "sample_capture_stage",
                "policy_value_core",
                "td_update_core",
                "result_stream_stage",
            ],
        )
        self.assertIn(
            {"from": "td_update_core.updated_value", "to": "result_stream_stage.updated_value"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire sample_valid", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] next_value", project.files["rtl/top.v"])
        self.assertIn("output wire result_valid", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] updated_value", project.files["rtl/top.v"])
        self.assertIn("output wire irq", project.files["rtl/top.v"])
        self.assertIn("expect_result(1'b0, 8'd7, 8'd7, 1'b0)", project.files["sim/tb_top.v"])
        self.assertIn("expect_result(1'b1, 8'd9, 8'd11, 1'b1)", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 30)

    def test_generates_composed_batch_rl_accelerator_shell_from_t11_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_batch_rl_accelerator_shell",
                width=8,
                project_name="composed_batch_rl_accelerator_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_batch_rl_accelerator_shell",
            {
                "rtl/top.v",
                "rtl/batch_config_bank.v",
                "rtl/batch_sample_buffer.v",
                "rtl/dual_policy_value_core.v",
                "rtl/dual_td_update_core.v",
                "rtl/batch_result_stage.v",
            },
            [
                "batch_config_bank",
                "batch_sample_buffer",
                "dual_policy_value_core",
                "dual_td_update_core",
                "batch_result_stage",
                ".cfg_valid(cfg_valid)",
                ".in_valid(batch_valid)",
                ".result_valid(result_valid)",
                ".updated_value_b_out(updated_value_b)",
                ".irq(irq)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t11_batch_rl_accelerator_shell")
        self.assertEqual(architecture["difficulty_tier"], "T4")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            [
                "batch_config_bank",
                "batch_sample_buffer",
                "dual_policy_value_core",
                "dual_td_update_core",
                "batch_result_stage",
            ],
        )
        self.assertIn(
            {"from": "dual_td_update_core.updated_value_b", "to": "batch_result_stage.updated_value_b"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire batch_valid", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] next_value_b", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] updated_value_a", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] updated_value_b", project.files["rtl/top.v"])
        self.assertIn("output wire batch_done", project.files["rtl/top.v"])
        self.assertIn("expect_batch_result(1'b0, 8'd7, 8'd7, 1'b1, 8'd9, 8'd11, 1'b1)", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 36)

    def test_generates_composed_replay_arbiter_shell_from_t12_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_replay_arbiter_shell",
                width=8,
                project_name="composed_replay_arbiter_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_replay_arbiter_shell",
            {
                "rtl/top.v",
                "rtl/host_transition_packetizer.v",
                "rtl/replay_index_allocator.v",
                "rtl/replay_request_arbiter.v",
                "rtl/replay_memory_bank.v",
                "rtl/sample_packet_stage.v",
            },
            [
                "host_transition_packetizer",
                "replay_index_allocator",
                "replay_request_arbiter",
                "replay_memory_bank",
                "sample_packet_stage",
                ".host_valid(host_valid)",
                ".read_req_valid(sample_req_valid)",
                ".sample_valid(sample_valid)",
                ".sample_state_out(sample_state)",
                ".irq(irq)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t12_replay_arbiter_shell")
        self.assertEqual(architecture["difficulty_tier"], "T4")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            [
                "host_transition_packetizer",
                "replay_index_allocator",
                "replay_request_arbiter",
                "replay_memory_bank",
                "sample_packet_stage",
            ],
        )
        self.assertIn(
            {"from": "replay_request_arbiter.mem_read_valid", "to": "replay_memory_bank.read_valid"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire host_valid", project.files["rtl/top.v"])
        self.assertIn("input wire sample_req_valid", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] sample_state", project.files["rtl/top.v"])
        self.assertIn("output wire [2:0] occupancy", project.files["rtl/top.v"])
        self.assertIn("output wire irq", project.files["rtl/top.v"])
        self.assertIn("expect_sample(8'h12, 1'b0, 8'h03, 8'h21, 1'b0)", project.files["sim/tb_top.v"])
        self.assertIn("expect_sample(8'h34, 1'b1, 8'h05, 8'h43, 1'b1)", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 34)

    def test_manifest_sources_exist_for_all_supported_task_types(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                _assert_manifest_sources_exist(self, project)
                self.assertEqual(_manifest(project)["simulation"]["testbench"], "sim/tb_top.v")
                self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_all_supported_task_types_have_explicit_t0_to_t4_difficulty_tier(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                architecture = _system_his(project)["architecture"]

                self.assertIn(architecture["difficulty_tier"], {"T0", "T1", "T2", "T3", "T4"})
                if not task_type.startswith("composed_"):
                    self.assertEqual(architecture["difficulty_tier"], "T0")

    def test_t0_t4_task_catalog_matches_supported_generator_cases(self) -> None:
        catalog = json.loads(Path("docs/sr2fpga-t0-t4-task-catalog.json").read_text(encoding="utf-8"))
        entries = catalog["tasks"]
        supported_cases = _supported_task_cases()

        self.assertEqual(catalog["taxonomy"], "T0-T4")
        self.assertEqual(len(entries), len(supported_cases))
        self.assertEqual([entry["task_type"] for entry in entries], [task_type for task_type, _, _ in supported_cases])

        supported_widths = {task_type: width for task_type, width, _ in supported_cases}
        for entry in entries:
            task_type = entry["task_type"]
            self.assertEqual(entry["default_width"], supported_widths[task_type])
            self.assertIn(entry["tier"], {"T0", "T1", "T2", "T3", "T4"})
            self.assertTrue(entry["rtl_category"])
            self.assertTrue(entry["testbench_oracle"])

            if task_type in COMPONENT_TOPOLOGIES:
                topology = COMPONENT_TOPOLOGIES[task_type]
                self.assertEqual(entry["topology_id"], topology["topology_id"])
                self.assertEqual(entry["tier"], topology["difficulty_tier"])
            else:
                self.assertIsNone(entry["topology_id"])
                self.assertEqual(entry["tier"], "T0")

    def test_all_generated_testbenches_are_black_box_io_oracles_with_timeout(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                testbench = project.files["sim/tb_top.v"]
                static_issues = check_testbench_static_issues(testbench)

                self.assertIn("top dut", testbench)
                self.assertNotRegex(testbench, r"\bdut\.")
                self.assertIn("TEST_PASS", testbench)
                self.assertIn("TEST_FAIL", testbench)
                self.assertIn("TEST_FAIL timeout", testbench)
                self.assertRegex(testbench, r"!==|!=")
                self.assertEqual(static_issues, [])

    def test_system_his_architecture_submodules_match_emitted_rtl_modules(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                architecture = _system_his(project)["architecture"]
                actual_submodules = sorted(_non_top_rtl_module_names(project))

                self.assertEqual(architecture["top_module"], "top")
                self.assertEqual(sorted(architecture["submodules"]), actual_submodules)
                expected_style = "multi_module" if actual_submodules else "single_module"
                self.assertEqual(architecture["style"], expected_style)

    def test_system_his_v12_declares_modules_ports_and_connections(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                system_his = _system_his(project)
                manifest = _manifest(project)
                actual_modules = set(_rtl_module_names(project))
                declared_modules = {module["name"] for module in system_his["modules"]}

                self.assertEqual(system_his["schema_version"], "system-his-v1.2")
                for key in (
                    "intent",
                    "top",
                    "state",
                    "components",
                    "instances",
                    "data_flow",
                    "control_flow",
                    "timing",
                    "resources",
                    "artifacts",
                ):
                    self.assertIn(key, system_his)
                self.assertEqual(
                    system_his["project"],
                    {
                        "name": project_name,
                        "description": system_his["system"]["description"],
                        "top": manifest["top_module"],
                    },
                )
                self.assertEqual(system_his["clocks"], [{"name": "clk", "target_fmax_mhz": 100.0}])
                self.assertEqual(system_his["resets"], [{"name": "rst_n", "polarity": "active_low", "kind": "async"}])
                self.assertEqual(system_his["top_ports"], _top_ports_from_interface(system_his["interface"]))
                self.assertEqual(system_his["qor_intent"]["resources"], _predicted_resources(project))
                self.assertEqual(system_his["verification"]["testbench"], "sim/tb_top.v")
                self.assertEqual(
                    system_his["verification"]["checks"],
                    ["l0_contract", "l1_lint", "l2_self_checking_sim", "l3_synthesis"],
                )
                self.assertIn("TEST_PASS", system_his["verification"]["test_pass_means"])
                self.assertEqual(
                    system_his["verification"]["test_pass_means"],
                    system_his["verification"]["expected_behavior"],
                )
                self.assertEqual(declared_modules, actual_modules)
                self.assertEqual(system_his["modules"][0]["name"], manifest["top_module"])
                self.assertEqual(system_his["modules"][0]["role"], "top")
                self.assertEqual(system_his["modules"][0]["source"], "rtl/top.v")
                self.assertEqual(system_his["modules"][0]["ports"], _top_ports_from_interface(system_his["interface"]))
                ports_by_module = {module["name"]: {port["name"] for port in module["ports"]} for module in system_his["modules"]}
                for module in system_his["modules"]:
                    self.assertIn(module["source"], manifest["sources"])
                    self.assertIn(module["name"], actual_modules)
                    self.assertIsInstance(module["parameters"], dict)
                    self.assertEqual(module["params"], _params_from_parameters(module["parameters"]))
                    self.assertEqual(module["clock"], "clk")
                    self.assertEqual(module["reset"], "rst_n")
                    self.assertIsInstance(module["intent"], str)
                    self.assertTrue(module["intent"])
                    self.assertIsInstance(module["ports"], list)
                    self.assertGreater(len(module["ports"]), 0)
                for connection in system_his["connections"]:
                    self.assertIn(connection["from"]["module"], declared_modules)
                    self.assertIn(connection["to"]["module"], declared_modules)
                    self.assertIn("signal", connection)
                    self.assertEqual(connection["kind"], "port_connection")
                    self.assertIn(connection["protocol"], {"register", "valid_ready"})
                    self.assertIn("width", connection)
                    self.assertFalse(connection["cdc"])
                    self.assertIn(connection["from"]["port"], ports_by_module[connection["from"]["module"]])
                    self.assertIn(connection["to"]["port"], ports_by_module[connection["to"]["module"]])

    def test_system_his_records_top_level_instance_parameter_overrides(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_stream_accumulator",
                width=8,
                project_name="composed_stream_accumulator_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        modules = {module["name"]: module for module in _system_his(project)["modules"]}

        self.assertEqual(modules["top"]["parameters"], {})
        self.assertEqual(modules["skid_buffer"]["parameters"], {"WIDTH": 8})
        self.assertEqual(modules["accumulator_core"]["parameters"], {"WIDTH": 8, "SUM_WIDTH": 12})

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_basic_generated_testbenches_pass_under_icarus(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("counter", 8, "counter_8bit"),
            ("fifo", 8, "fifo_8bit"),
            ("simple_fsm", 4, "fsm_sequence_4bit"),
            ("ram_read_write", 16, "ram_rw_16bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                with tempfile.TemporaryDirectory() as tmp:
                    project_dir = Path(tmp)
                    _write_project(project_dir, project)
                    manifest = _manifest(project)
                    compile_result = subprocess.run(
                        [
                            "iverilog",
                            "-g2012",
                            "-o",
                            "sim.out",
                            *manifest["sources"],
                            manifest["simulation"]["testbench"],
                        ],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(
                        compile_result.returncode,
                        0,
                        f"{task_type} sim compile failed\n"
                        f"STDOUT:\n{compile_result.stdout}\n"
                        f"STDERR:\n{compile_result.stderr}",
                    )
                    run_result = subprocess.run(
                        ["vvp", "sim.out"],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(
                    run_result.returncode,
                    0,
                    f"{task_type} sim run failed\nSTDOUT:\n{run_result.stdout}\nSTDERR:\n{run_result.stderr}",
                )
                self.assertIn("TEST_PASS", run_result.stdout)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_multimodule_generated_testbenches_pass_under_icarus(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("uart_tx", 8, "uart_tx_8bit"),
            ("spi_master", 8, "spi_master_8bit"),
            ("pwm_controller", 8, "pwm_controller_8bit"),
            ("fir_filter", 8, "fir_filter_8bit"),
            ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
            ("matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
            ("alu_control_unit", 8, "alu_control_unit_8bit"),
            ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
            ("composed_stream_fork", 8, "composed_stream_fork_8bit"),
            ("composed_dual_stream_join", 8, "composed_dual_stream_join_8bit"),
            ("composed_vector_mac_pipeline", 8, "composed_vector_mac_pipeline_8bit"),
            ("composed_td_update_core", 8, "composed_td_update_core_8bit"),
            ("composed_policy_value_shell", 8, "composed_policy_value_shell_8bit"),
            ("composed_replay_sample_shell", 8, "composed_replay_sample_shell_8bit"),
            ("composed_host_protocol_shell", 8, "composed_host_protocol_shell_8bit"),
            ("composed_rl_accelerator_shell", 8, "composed_rl_accelerator_shell_8bit"),
            ("composed_batch_rl_accelerator_shell", 8, "composed_batch_rl_accelerator_shell_8bit"),
            ("composed_replay_arbiter_shell", 8, "composed_replay_arbiter_shell_8bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                with tempfile.TemporaryDirectory() as tmp:
                    project_dir = Path(tmp)
                    _write_project(project_dir, project)
                    manifest = _manifest(project)
                    compile_result = subprocess.run(
                        [
                            "iverilog",
                            "-g2012",
                            "-o",
                            "sim.out",
                            *manifest["sources"],
                            manifest["simulation"]["testbench"],
                        ],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(
                        compile_result.returncode,
                        0,
                        f"{task_type} sim compile failed\n"
                        f"STDOUT:\n{compile_result.stdout}\n"
                        f"STDERR:\n{compile_result.stderr}",
                    )
                    run_result = subprocess.run(
                        ["vvp", "sim.out"],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(
                    run_result.returncode,
                    0,
                    f"{task_type} sim run failed\nSTDOUT:\n{run_result.stdout}\nSTDERR:\n{run_result.stderr}",
                )
                self.assertIn("TEST_PASS", run_result.stdout)

    @unittest.skipUnless(shutil.which("verilator"), "verilator is not installed")
    def test_multimodule_task_sources_are_verilator_wall_clean(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("uart_tx", 8, "uart_tx_8bit"),
            ("spi_master", 8, "spi_master_8bit"),
            ("pwm_controller", 8, "pwm_controller_8bit"),
            ("fir_filter", 8, "fir_filter_8bit"),
            ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
            ("matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
            ("alu_control_unit", 8, "alu_control_unit_8bit"),
            ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
            ("composed_event_counter", 8, "composed_event_counter_8bit"),
            ("composed_stream_accumulator", 8, "composed_stream_accumulator_8bit"),
            ("composed_stream_fork", 8, "composed_stream_fork_8bit"),
            ("composed_dual_stream_join", 8, "composed_dual_stream_join_8bit"),
            ("composed_vector_mac_pipeline", 8, "composed_vector_mac_pipeline_8bit"),
            ("composed_td_update_core", 8, "composed_td_update_core_8bit"),
            ("composed_policy_value_shell", 8, "composed_policy_value_shell_8bit"),
            ("composed_replay_sample_shell", 8, "composed_replay_sample_shell_8bit"),
            ("composed_host_protocol_shell", 8, "composed_host_protocol_shell_8bit"),
            ("composed_rl_accelerator_shell", 8, "composed_rl_accelerator_shell_8bit"),
            ("composed_batch_rl_accelerator_shell", 8, "composed_batch_rl_accelerator_shell_8bit"),
            ("composed_replay_arbiter_shell", 8, "composed_replay_arbiter_shell_8bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                with tempfile.TemporaryDirectory() as tmp:
                    project_dir = Path(tmp)
                    _write_project(project_dir, project)
                    manifest = _manifest(project)
                    result = subprocess.run(
                        ["verilator", "--lint-only", "-Wall", *manifest["sources"]],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{task_type} lint failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                )


def _task_type(project) -> str:
    return json.loads(project.files["system_his.json"])["task_type"]


def _manifest(project) -> dict:
    return json.loads(project.files["manifest.json"])


def _system_his(project) -> dict:
    return json.loads(project.files["system_his.json"])


def _predicted_resources(project) -> dict:
    predicted = json.loads(project.files["reports/predicted_qor.json"])["predicted"]
    return {key: predicted[key] for key in ("lut", "ff", "bram", "dsp")}


def _supported_task_cases() -> list[tuple[str, int, str]]:
    return [
        ("counter", 8, "counter_8bit"),
        ("fifo", 8, "fifo_8bit"),
        ("simple_fsm", 4, "fsm_sequence_4bit"),
        ("ram_read_write", 16, "ram_rw_16bit"),
        ("uart_tx", 8, "uart_tx_8bit"),
        ("spi_master", 8, "spi_master_8bit"),
        ("pwm_controller", 8, "pwm_controller_8bit"),
        ("fir_filter", 8, "fir_filter_8bit"),
        ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
        ("matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
        ("alu_control_unit", 8, "alu_control_unit_8bit"),
        ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
        ("composed_event_counter", 8, "composed_event_counter_8bit"),
        ("composed_stream_accumulator", 8, "composed_stream_accumulator_8bit"),
        ("composed_stream_fork", 8, "composed_stream_fork_8bit"),
        ("composed_dual_stream_join", 8, "composed_dual_stream_join_8bit"),
        ("composed_vector_mac_pipeline", 8, "composed_vector_mac_pipeline_8bit"),
        ("composed_td_update_core", 8, "composed_td_update_core_8bit"),
        ("composed_policy_value_shell", 8, "composed_policy_value_shell_8bit"),
        ("composed_replay_sample_shell", 8, "composed_replay_sample_shell_8bit"),
        ("composed_host_protocol_shell", 8, "composed_host_protocol_shell_8bit"),
        ("composed_rl_accelerator_shell", 8, "composed_rl_accelerator_shell_8bit"),
        ("composed_batch_rl_accelerator_shell", 8, "composed_batch_rl_accelerator_shell_8bit"),
        ("composed_replay_arbiter_shell", 8, "composed_replay_arbiter_shell_8bit"),
    ]


def _non_top_rtl_module_names(project) -> list[str]:
    names = []
    for source in _manifest(project)["sources"]:
        for match in re.finditer(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_$]*)\b", project.files[source]):
            if match.group(1) != "top":
                names.append(match.group(1))
    return names


def _rtl_module_names(project) -> list[str]:
    names = []
    for source in _manifest(project)["sources"]:
        for match in re.finditer(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_$]*)\b", project.files[source]):
            names.append(match.group(1))
    return names


def _top_ports_from_interface(interface: dict) -> list[dict[str, object]]:
    ports = []
    for direction in ("inputs", "outputs"):
        for port in interface[direction]:
            ports.append(
                {
                    "name": port["name"],
                    "direction": "input" if direction == "inputs" else "output",
                    "width": port["width"],
                }
            )
    return ports


def _params_from_parameters(parameters: dict[str, object]) -> list[dict[str, object]]:
    return [{"name": name, "value": value} for name, value in parameters.items()]


def _assert_manifest_sources_exist(testcase: unittest.TestCase, project) -> None:
    manifest = _manifest(project)
    rtl_sources = sorted(path for path in project.files if path.startswith("rtl/"))
    testcase.assertEqual(sorted(manifest["sources"]), rtl_sources)
    testcase.assertIn("rtl/top.v", manifest["sources"])
    for source in manifest["sources"]:
        testcase.assertIn(source, project.files)
        testcase.assertTrue(source.startswith("rtl/"), source)
        testcase.assertIn("module ", project.files[source])


def _assert_multimodule_task(
    testcase: unittest.TestCase,
    project,
    task_type: str,
    expected_sources: set[str],
    top_markers: list[str],
) -> None:
    manifest = _manifest(project)
    system_his = _system_his(project)
    testcase.assertEqual(system_his["task_type"], task_type)
    testcase.assertTrue(expected_sources.issubset(set(manifest["sources"])))
    testcase.assertTrue(expected_sources.issubset(set(project.files)))
    testcase.assertGreater(len(manifest["sources"]), 1)
    testcase.assertIn("architecture", system_his)
    testcase.assertIn("submodules", system_his["architecture"])
    for marker in top_markers:
        testcase.assertIn(marker, project.files["rtl/top.v"])
    testcase.assertIn("TEST_PASS", project.files["sim/tb_top.v"])


def _write_project(project_dir: Path, project) -> None:
    for relative_path, content in project.files.items():
        target = project_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
