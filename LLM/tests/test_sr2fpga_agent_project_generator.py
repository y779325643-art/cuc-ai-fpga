import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent import PlatformProfile, ProjectGenerator, ProjectRequest
from LLM.src.sr2fpga_agent import project_generator as project_generator_module
from LLM.src.sr2fpga_agent.project_generator import (
    COMPONENT_TOPOLOGIES,
    SUPPORTED_TASK_TYPES,
    TASK_TYPE_ALIASES,
)
from LLM.src.sr2fpga_agent.task_families import (
    FAMILY_IDS,
    TASK_FAMILY_IDS,
    family_id_for_task_type,
)
from LLM.src.sr2fpga_agent.task_families import basic, datapath, image, protocol, rl, stream
from LLM.src.sr2fpga_agent.task_catalog import task_family_spec_for_family_id
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0
from LLM.src.sr2fpga_agent.his_validation import validate_system_his_h_stages
from LLM.src.sr2fpga_agent.testbench_checker import check_testbench_static_issues


class ProjectGeneratorTest(unittest.TestCase):
    def test_system_his_architecture_uses_catalog_generation_contract(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="fir_filter",
                width=8,
                project_name="fir_catalog_contract",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        architecture = _system_his(project)["architecture"]
        self.assertEqual(architecture["task_family_id"], "fir_filter")
        self.assertEqual(architecture["difficulty_tier"], "T3")
        self.assertEqual(architecture["system_his_profile"], "streaming_datapath")
        self.assertEqual(architecture["skeleton_level"], "S2_protocol_skeleton")
        self.assertEqual(
            architecture["oracle_kind"],
            ["python_numpy_golden", "transaction_scoreboard"],
        )

    def test_task_families_expose_stable_ids_for_current_generator_tasks(self) -> None:
        expected_family_ids = {
            "binary_bcd_counter",
            "sync_fifo",
            "simple_fsm",
            "single_dual_port_ram",
            "uart_tx",
            "uart_rx",
            "uart_fifo_loopback",
            "spi_master",
            "pwm_generator",
            "fir_filter",
            "matched_filter",
            "peak_detector",
            "p_pulse_radar_signal",
            "valid_ready_stream_accumulator",
            "valid_ready_stream_stage",
            "matrix_vector_mac",
            "alu_control_unit",
            "crc_stream_checker",
            "t1_event_counter",
            "stream_fork_join",
            "mac_array",
            "qtable_update_core",
            "rl_reward_policy_update",
            "t8_replay_sample_shell",
            "t9_host_protocol_shell",
            "p_rl_qlearning_accel",
            "t12_replay_arbiter_shell",
            "sobel_threshold",
            "p_vision_defect_core",
            "pattern_matcher",
            "p_stream_trigger_filter",
        }

        self.assertEqual(set(TASK_FAMILY_IDS), set(SUPPORTED_TASK_TYPES) - set(TASK_TYPE_ALIASES))
        self.assertEqual(FAMILY_IDS, expected_family_ids)

    def test_family_modules_own_executable_generation_helpers(self) -> None:
        self.assertIs(project_generator_module._counter_rtl, basic.counter_rtl)
        self.assertIs(project_generator_module._counter_testbench, basic.counter_testbench)
        self.assertIs(project_generator_module._simple_fsm_rtl, basic.simple_fsm_rtl)
        self.assertIs(project_generator_module._simple_fsm_testbench, basic.simple_fsm_testbench)
        self.assertIs(project_generator_module._ram_read_write_rtl, basic.ram_read_write_rtl)
        self.assertIs(project_generator_module._ram_read_write_testbench, basic.ram_read_write_testbench)
        self.assertIs(project_generator_module._fifo_rtl, protocol.fifo_rtl)
        self.assertIs(project_generator_module._fifo_testbench, protocol.fifo_testbench)
        self.assertIs(project_generator_module._uart_tx_rtl_files, protocol.uart_tx_rtl_files)
        self.assertIs(project_generator_module._uart_tx_testbench, protocol.uart_tx_testbench)
        self.assertIs(project_generator_module._spi_master_rtl_files, protocol.spi_master_rtl_files)
        self.assertIs(project_generator_module._spi_master_testbench, protocol.spi_master_testbench)
        self.assertIs(project_generator_module._pwm_controller_rtl_files, datapath.pwm_controller_rtl_files)
        self.assertIs(project_generator_module._pwm_controller_testbench, datapath.pwm_controller_testbench)
        self.assertIs(
            project_generator_module._composed_vector_mac_pipeline_rtl_files,
            datapath.composed_vector_mac_pipeline_rtl_files,
        )
        self.assertIs(
            project_generator_module._composed_vector_mac_pipeline_testbench,
            datapath.composed_vector_mac_pipeline_testbench,
        )
        self.assertIs(project_generator_module._fir_filter_rtl_files, datapath.fir_filter_rtl_files)
        self.assertIs(project_generator_module._fir_filter_testbench, datapath.fir_filter_testbench)
        self.assertIs(
            project_generator_module._matrix_vector_mac_rtl_files,
            datapath.matrix_vector_mac_rtl_files,
        )
        self.assertIs(
            project_generator_module._matrix_vector_mac_testbench,
            datapath.matrix_vector_mac_testbench,
        )
        self.assertIs(
            project_generator_module._alu_control_unit_rtl_files,
            datapath.alu_control_unit_rtl_files,
        )
        self.assertIs(
            project_generator_module._alu_control_unit_testbench,
            datapath.alu_control_unit_testbench,
        )
        self.assertIs(
            project_generator_module._crc_stream_checker_rtl_files,
            datapath.crc_stream_checker_rtl_files,
        )
        self.assertIs(
            project_generator_module._crc_stream_checker_testbench,
            datapath.crc_stream_checker_testbench,
        )
        self.assertIs(
            project_generator_module._streaming_valid_ready_testbench,
            stream.streaming_valid_ready_testbench,
        )
        self.assertIs(
            project_generator_module._streaming_valid_ready_rtl_files,
            stream.streaming_valid_ready_rtl_files,
        )
        self.assertIs(
            project_generator_module._composed_stream_accumulator_testbench,
            stream.composed_stream_accumulator_testbench,
        )
        self.assertIs(
            project_generator_module._composed_stream_accumulator_rtl_files,
            stream.composed_stream_accumulator_rtl_files,
        )
        self.assertIs(
            project_generator_module._composed_event_counter_testbench,
            stream.composed_event_counter_testbench,
        )
        self.assertIs(
            project_generator_module._composed_event_counter_rtl_files,
            stream.composed_event_counter_rtl_files,
        )
        self.assertIs(
            project_generator_module._composed_stream_fork_testbench,
            stream.composed_stream_fork_testbench,
        )
        self.assertIs(
            project_generator_module._composed_stream_fork_rtl_files,
            stream.composed_stream_fork_rtl_files,
        )
        self.assertIs(
            project_generator_module._composed_dual_stream_join_testbench,
            stream.composed_dual_stream_join_testbench,
        )
        self.assertIs(
            project_generator_module._composed_dual_stream_join_rtl_files,
            stream.composed_dual_stream_join_rtl_files,
        )
        self.assertIs(project_generator_module._batch_config_bank_rtl, rl.batch_config_bank_rtl)
        for facade_name, owner_name in (
            ("_composed_td_update_core_testbench", "composed_td_update_core_testbench"),
            ("_composed_policy_value_shell_testbench", "composed_policy_value_shell_testbench"),
            ("_composed_replay_sample_shell_testbench", "composed_replay_sample_shell_testbench"),
            ("_composed_host_protocol_shell_testbench", "composed_host_protocol_shell_testbench"),
            ("_composed_rl_accelerator_shell_testbench", "composed_rl_accelerator_shell_testbench"),
            (
                "_composed_batch_rl_accelerator_shell_testbench",
                "composed_batch_rl_accelerator_shell_testbench",
            ),
            ("_composed_replay_arbiter_shell_testbench", "composed_replay_arbiter_shell_testbench"),
            ("_composed_td_update_core_rtl_files", "composed_td_update_core_rtl_files"),
            ("_composed_policy_value_shell_rtl_files", "composed_policy_value_shell_rtl_files"),
            ("_composed_replay_sample_shell_rtl_files", "composed_replay_sample_shell_rtl_files"),
            ("_composed_host_protocol_shell_rtl_files", "composed_host_protocol_shell_rtl_files"),
            ("_composed_rl_accelerator_shell_rtl_files", "composed_rl_accelerator_shell_rtl_files"),
            (
                "_composed_batch_rl_accelerator_shell_rtl_files",
                "composed_batch_rl_accelerator_shell_rtl_files",
            ),
            ("_composed_replay_arbiter_shell_rtl_files", "composed_replay_arbiter_shell_rtl_files"),
        ):
            self.assertIs(getattr(project_generator_module, facade_name), getattr(rl, owner_name))

    def test_task_type_alias_canonical_values_map_to_stable_family_ids(self) -> None:
        for alias, canonical_task_type in TASK_TYPE_ALIASES.items():
            with self.subTest(alias=alias):
                self.assertIn(canonical_task_type, TASK_FAMILY_IDS)
                self.assertEqual(
                    family_id_for_task_type(alias),
                    family_id_for_task_type(canonical_task_type),
                )

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
        self.assertIn(
            'TEST_FAIL signal=count cycle=4 expected=4 actual=%0d',
            testbench,
        )

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
        self.assertIn("fifo should be full after four writes", project.files["sim/tb_top.v"])
        self.assertIn("overflow guard changed stored data", project.files["sim/tb_top.v"])
        self.assertIn("underflow guard advanced read pointer", project.files["sim/tb_top.v"])
        self.assertIn("simultaneous push-pop changed occupancy", project.files["sim/tb_top.v"])

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
            ("uart_rx", 8, "uart_rx_8bit"),
            ("uart_fifo_loopback", 8, "uart_fifo_loopback_8bit"),
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
        self.assertIn("8'h96", project.files["sim/tb_top.v"])

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
        self.assertIn("tx_data = 8'h96", project.files["sim/tb_top.v"])

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
            [
                "fir_filter_core",
                "mac_unit",
                ".sample_valid(sample_valid)",
                ".sample_ready(sample_ready)",
                ".result_valid(result_valid)",
                ".result_ready(result_ready)",
            ],
        )
        top_rtl = project.files["rtl/top.v"]
        core_rtl = project.files["rtl/fir_filter_core.v"]
        mac_rtl = project.files["rtl/mac_unit.v"]
        testbench = project.files["sim/tb_top.v"]
        self.assertIn("input wire signed [7:0] sample", top_rtl)
        self.assertIn("output wire sample_ready", top_rtl)
        self.assertIn("input wire result_ready", top_rtl)
        self.assertIn("output wire signed [10:0] result", top_rtl)
        self.assertIn("COEFF_NEW = 3'sd3", core_rtl)
        self.assertIn("COEFF_PREV = -3'sd2", core_rtl)
        self.assertIn("COEFF_OLD = 3'sd1", core_rtl)
        self.assertIn("else if (sample_ready) begin", core_rtl)
        self.assertIn("$signed(sample) * $signed(coefficient)", mac_rtl)
        self.assertIn("TEST_FAIL result changed under backpressure", testbench)
        self.assertIn("send_and_expect(-8'sd4, -11'sd22)", testbench)
        self.assertIn("send_and_expect(8'sd127, 11'sd381)", testbench)
        self.assertIn("TEST_PASS", testbench)

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
            [
                "dot_product_engine",
                "mac_unit",
                "vector_rom",
                ".sample_valid(sample_valid)",
                ".sample_ready(sample_ready)",
                ".result_valid(result_valid)",
                ".result_ready(result_ready)",
            ],
        )
        top_rtl = project.files["rtl/top.v"]
        engine_rtl = project.files["rtl/dot_product_engine.v"]
        mac_rtl = project.files["rtl/mac_unit.v"]
        rom_rtl = project.files["rtl/vector_rom.v"]
        testbench = project.files["sim/tb_top.v"]
        self.assertIn("input wire signed [7:0] sample", top_rtl)
        self.assertIn("output wire sample_ready", top_rtl)
        self.assertIn("input wire result_ready", top_rtl)
        self.assertIn("output wire signed [11:0] result", top_rtl)
        self.assertIn("assign sample_ready = !result_valid || result_ready;", engine_rtl)
        self.assertIn("sample_valid && sample_ready", engine_rtl)
        self.assertIn("$signed(sample) * $signed(coefficient)", mac_rtl)
        self.assertIn("2'd1: coefficient = -3'sd1", rom_rtl)
        self.assertIn("8'sd1, 8'sd2, 8'sd3, 8'sd4, 12'sd13", testbench)
        self.assertIn("TEST_FAIL accepted sample while result stalled", testbench)

    def test_mac_array_alias_generates_matrix_vector_mac_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="mac_array", width=8, project_name="mac_array_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "matrix_vector_mac",
            {"rtl/top.v", "rtl/dot_product_engine.v", "rtl/mac_unit.v", "rtl/vector_rom.v"},
            ["dot_product_engine", "mac_unit", "vector_rom", ".sample_ready(sample_ready)"],
        )
        self.assertEqual(project.project_name, "mac_array_8bit")
        self.assertTrue(check_project_l0(project).passed, check_project_l0(project).errors)
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
        self.assertEqual(architecture["difficulty_tier"], "T2")
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
        self.assertEqual(architecture["difficulty_tier"], "T4")
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

    def test_all_supported_task_types_use_catalog_generation_contract(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                architecture = _system_his(project)["architecture"]
                family_id = family_id_for_task_type(task_type)
                family = task_family_spec_for_family_id(family_id)

                self.assertEqual(architecture["task_family_id"], family.family_id)
                self.assertEqual(architecture["difficulty_tier"], family.sr2fpga_tier)
                self.assertEqual(architecture["system_his_profile"], family.system_his_profile)
                self.assertEqual(architecture["skeleton_level"], family.skeleton_level)
                self.assertEqual(architecture["oracle_kind"], list(family.oracle_kind))

    def test_legacy_t0_t4_catalog_still_covers_supported_generator_cases(self) -> None:
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
            else:
                self.assertIsNone(entry["topology_id"])

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
            ("uart_rx", 8, "uart_rx_8bit"),
            ("uart_fifo_loopback", 8, "uart_fifo_loopback_8bit"),
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

    def test_phase_b_uart_rx_and_uart_fifo_loopback_generate_contract_valid_projects(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = (
            ("uart_rx", "uart_rx"),
            ("uart_fifo_loopback", "uart_fifo_loopback"),
        )

        for task_type, family_id in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_{task_type}"),
                    platform,
                )

                his = _system_his(project)
                manifest = _manifest(project)
                self.assertEqual(his["architecture"]["task_family_id"], family_id)
                self.assertEqual(manifest["top_module"], "top")
                self.assertIn("sim/tb_top.v", project.files)
                self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
                self.assertNotIn("dut.", project.files["sim/tb_top.v"])
                self.assertNotIn("uut.", project.files["sim/tb_top.v"])
                if task_type == "uart_rx":
                    self.assertNotIn("#1;", project.files["sim/tb_top.v"])
                    self.assertIn("repeat (1) @(negedge clk);", project.files["sim/tb_top.v"])
                _assert_manifest_sources_exist(self, project)
                self.assertEqual(
                    set(his["artifacts"]["rtl_sources"]),
                    set(manifest["sources"]),
                )
                l0_result = check_project_l0(project)
                self.assertTrue(l0_result.passed, l0_result.errors)

    def test_phase_b_core_closure_projects_are_h2_lowerable_and_verilator_clean(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        task_types = (
            "uart_rx",
            "uart_fifo_loopback",
            "matched_filter",
            "peak_detector",
            "pulse_radar_signal",
            "sobel_threshold",
            "vision_defect_core",
            "pattern_matcher",
            "stream_trigger_filter",
        )

        for task_type in task_types:
            with self.subTest(task_type=task_type):
                request = ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_ready_{task_type}")
                project = ProjectGenerator().generate(request, platform)
                his_report = validate_system_his_h_stages(request, project)
                self.assertEqual(his_report["h0"]["status"], "pass")
                self.assertEqual(his_report["h1"]["status"], "pass")
                self.assertEqual(his_report["h2"]["status"], "pass", his_report["h2"]["diagnostics"])
                with tempfile.TemporaryDirectory() as tmp:
                    project_dir = Path(tmp)
                    _write_project(project_dir, project)
                    result = subprocess.run(
                        ["verilator", "--lint-only", "-Wall", *_manifest(project)["sources"]],
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

    def test_phase_b_uart_rx_and_uart_fifo_loopback_expose_exact_top_interfaces(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = (
            ("uart_rx", {"clk", "rst_n", "rx", "data", "data_valid", "framing_error"}),
            ("uart_fifo_loopback", {"clk", "rst_n", "rx", "tx", "tx_enable"}),
        )

        for task_type, expected_ports in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_{task_type}_ports"),
                    platform,
                )

                interface = _system_his(project)["interface"]
                ports = {port["name"] for port in _top_ports_from_interface(interface)}
                self.assertEqual(ports, expected_ports)

    def test_phase_b_matched_filter_peak_detector_and_pulse_radar_generate_contract_valid_projects(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = (
            ("matched_filter", "matched_filter"),
            ("peak_detector", "peak_detector"),
            ("pulse_radar_signal", "p_pulse_radar_signal"),
        )

        for task_type, family_id in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_{task_type}"),
                    platform,
                )

                his = _system_his(project)
                manifest = _manifest(project)
                self.assertEqual(his["architecture"]["task_family_id"], family_id)
                self.assertEqual(
                    set(manifest["sources"]),
                    {path for path in project.files if path.startswith("rtl/")},
                )
                self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
                self.assertNotIn("dut.", project.files["sim/tb_top.v"])
                self.assertNotIn("uut.", project.files["sim/tb_top.v"])
                self.assertEqual(
                    set(his["artifacts"]["rtl_sources"]),
                    set(manifest["sources"]),
                )
                l0_result = check_project_l0(project)
                self.assertTrue(l0_result.passed, l0_result.errors)

    def test_phase_b_matched_filter_peak_detector_and_pulse_radar_expose_streaming_signed_interfaces_and_components(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = (
            (
                "matched_filter",
                {"clk", "rst_n", "in_valid", "in_ready", "in_sample", "out_valid", "out_ready", "correlation"},
                {"rtl/matched_filter_core.v", "rtl/matched_filter_mac.v"},
            ),
            (
                "peak_detector",
                {
                    "clk",
                    "rst_n",
                    "in_valid",
                    "in_ready",
                    "in_sample",
                    "in_last",
                    "out_valid",
                    "out_ready",
                    "peak_found",
                    "peak_value",
                    "peak_index",
                },
                {"rtl/peak_detector_core.v"},
            ),
            (
                "pulse_radar_signal",
                {
                    "clk",
                    "rst_n",
                    "in_valid",
                    "in_ready",
                    "in_sample",
                    "in_last",
                    "out_valid",
                    "out_ready",
                    "peak_found",
                    "peak_value",
                    "peak_index",
                },
                {"rtl/matched_filter_core.v", "rtl/matched_filter_mac.v", "rtl/threshold_comparator.v", "rtl/peak_detector_core.v"},
            ),
        )

        for task_type, expected_ports, expected_sources in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_{task_type}_ports"),
                    platform,
                )
                ports = {port["name"] for port in _top_ports_from_interface(_system_his(project)["interface"])}
                self.assertEqual(ports, expected_ports)
                self.assertTrue(expected_sources.issubset(project.files))

                top_rtl = project.files["rtl/top.v"]
                self.assertIn("input wire signed [7:0] in_sample", top_rtl)
                if task_type == "matched_filter":
                    core_rtl = project.files["rtl/matched_filter_core.v"]
                    self.assertIn("parameter TAP0 =", core_rtl)
                    self.assertIn("parameter TAP3 =", core_rtl)
                    self.assertIn("parameter ACC_WIDTH = 18", core_rtl)
                    self.assertNotIn("parameter signed", core_rtl)
                    self.assertNotIn("parameter integer", core_rtl)
                    self.assertIn("{{(ACC_WIDTH-WIDTH){in_sample[WIDTH-1]}}, in_sample}", core_rtl)
                    self.assertIn("assign in_ready = !out_valid || out_ready;", core_rtl)
                elif task_type == "peak_detector":
                    core_rtl = project.files["rtl/peak_detector_core.v"]
                    self.assertIn("input wire in_last", core_rtl)
                    self.assertIn("parameter THRESHOLD =", core_rtl)
                    self.assertIn("candidate_value > peak_value", core_rtl)
                else:
                    self.assertIn("matched_filter_core", top_rtl)
                    self.assertIn("threshold_comparator", top_rtl)
                    self.assertIn("peak_detector_core", top_rtl)
                    self.assertIn(".in_sample(correlation)", top_rtl)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_matched_filter_peak_detector_and_pulse_radar_embedded_black_box_testbenches_run(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        for task_type in ("matched_filter", "peak_detector", "pulse_radar_signal"):
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_{task_type}_sim"),
                    platform,
                )
                self.assertIn("TEST_PASS", _run_generated_testbench(project))

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_2a_matched_filter_contract_l0_and_embedded_black_box_testbench(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="matched_filter", width=8, project_name="phase_b_2a_matched_filter"),
            platform,
        )

        self.assertEqual(_system_his(project)["architecture"]["task_family_id"], "matched_filter")
        self.assertEqual(
            set(_manifest(project)["sources"]),
            {"rtl/top.v", "rtl/matched_filter_core.v", "rtl/matched_filter_mac.v"},
        )
        core_rtl = project.files["rtl/matched_filter_core.v"]
        self.assertIn("parameter TAP0 = -1", core_rtl)
        self.assertIn("parameter TAP3 = 4", core_rtl)
        self.assertIn("parameter ACC_WIDTH = 18", core_rtl)
        self.assertNotIn("parameter integer", core_rtl)
        self.assertNotIn("parameter signed", core_rtl)
        self.assertIn("{{(ACC_WIDTH-WIDTH){in_sample[WIDTH-1]}}, in_sample}", core_rtl)
        self.assertIn("assign in_ready = !out_valid || out_ready;", core_rtl)
        self.assertNotRegex(project.files["sim/tb_top.v"], r"\bdut\.")
        l0_result = check_project_l0(project)
        self.assertTrue(l0_result.passed, l0_result.errors)
        self.assertIn("TEST_PASS", _run_generated_testbench(project))

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_2b_peak_detector_contract_l0_and_embedded_black_box_testbench(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="peak_detector", width=8, project_name="phase_b_2b_peak_detector"),
            platform,
        )

        self.assertEqual(_system_his(project)["architecture"]["task_family_id"], "peak_detector")
        self.assertEqual(
            set(_manifest(project)["sources"]),
            {"rtl/top.v", "rtl/peak_detector_core.v"},
        )
        top_rtl = project.files["rtl/top.v"]
        core_rtl = project.files["rtl/peak_detector_core.v"]
        self.assertIn("input wire signed [7:0] in_sample", top_rtl)
        self.assertIn("input wire in_last", top_rtl)
        self.assertIn("output wire peak_found", top_rtl)
        self.assertIn("output wire signed [7:0] peak_value", top_rtl)
        self.assertIn("output wire [7:0] peak_index", top_rtl)
        self.assertIn("parameter THRESHOLD = 10", core_rtl)
        self.assertNotIn("parameter integer", core_rtl)
        self.assertNotIn("parameter signed", core_rtl)
        self.assertIn("assign in_ready = !out_valid || out_ready;", core_rtl)
        self.assertIn("candidate_value > peak_value", core_rtl)
        self.assertIn("peak_found <= 1'b0;", core_rtl)
        self.assertIn("peak_value <= {WIDTH{1'b0}};", core_rtl)
        self.assertIn("peak_index <= {WIDTH{1'b0}};", core_rtl)
        self.assertNotRegex(project.files["sim/tb_top.v"], r"\bdut\.")
        l0_result = check_project_l0(project)
        self.assertTrue(l0_result.passed, l0_result.errors)
        self.assertIn("TEST_PASS", _run_generated_testbench(project))

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_2c_pulse_radar_composes_aligned_streaming_cores(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="pulse_radar_signal", width=8, project_name="phase_b_2c_pulse_radar"),
            platform,
        )

        his = _system_his(project)
        self.assertEqual(his["architecture"]["task_family_id"], "p_pulse_radar_signal")
        self.assertEqual(
            set(_manifest(project)["sources"]),
            {
                "rtl/top.v",
                "rtl/matched_filter_core.v",
                "rtl/matched_filter_mac.v",
                "rtl/threshold_comparator.v",
                "rtl/peak_detector_core.v",
            },
        )
        top_rtl = project.files["rtl/top.v"]
        comparator_rtl = project.files["rtl/threshold_comparator.v"]
        self.assertIn(".out_last(correlation_last)", top_rtl)
        self.assertIn(".in_last(correlation_last)", top_rtl)
        self.assertIn(".out_last(threshold_last)", top_rtl)
        self.assertIn(".in_last(threshold_last)", top_rtl)
        self.assertIn("parameter THRESHOLD = 10", comparator_rtl)
        self.assertIn("wire signed [ACC_WIDTH-1:0] threshold_value", comparator_rtl)
        self.assertIn("$signed(in_sample) >= $signed(threshold_value)", comparator_rtl)
        self.assertIn("$signed(threshold_value) - $signed(one_value)", comparator_rtl)
        self.assertNotIn("dut.", project.files["sim/tb_top.v"])
        self.assertIn("negative correlation", project.files["sim/tb_top.v"].lower())
        self.assertIn("below threshold", project.files["sim/tb_top.v"].lower())
        self.assertEqual(
            {instance["name"] for instance in his["instances"]},
            {"u_matched_filter_core", "u_threshold_comparator", "u_peak_detector_core"},
        )
        paths = {tuple(flow["path"]) for flow in his["data_flow"]}
        self.assertIn(("u_matched_filter_core.out_correlation", "u_threshold_comparator.in_sample"), paths)
        self.assertIn(("u_threshold_comparator.out_sample", "u_peak_detector_core.in_sample"), paths)
        expected_edge_widths = {
            ("top.in_valid", "u_matched_filter_core.in_valid"): 1,
            ("top.in_sample", "u_matched_filter_core.in_sample"): 8,
            ("top.in_last", "u_matched_filter_core.in_last"): 1,
            ("u_matched_filter_core.in_ready", "top.in_ready"): 1,
            ("u_matched_filter_core.out_valid", "u_threshold_comparator.in_valid"): 1,
            ("u_matched_filter_core.out_correlation", "u_threshold_comparator.in_sample"): 18,
            ("u_matched_filter_core.out_last", "u_threshold_comparator.in_last"): 1,
            ("u_threshold_comparator.in_ready", "u_matched_filter_core.out_ready"): 1,
            ("u_threshold_comparator.out_valid", "u_peak_detector_core.in_valid"): 1,
            ("u_threshold_comparator.out_sample", "u_peak_detector_core.in_sample"): 18,
            ("u_threshold_comparator.out_last", "u_peak_detector_core.in_last"): 1,
            ("u_peak_detector_core.in_ready", "u_threshold_comparator.out_ready"): 1,
            ("u_peak_detector_core.out_valid", "top.out_valid"): 1,
            ("top.out_ready", "u_peak_detector_core.out_ready"): 1,
            ("u_peak_detector_core.out_peak_found", "top.peak_found"): 1,
            ("u_peak_detector_core.out_peak_value", "top.peak_value"): 18,
            ("u_peak_detector_core.out_peak_index", "top.peak_index"): 18,
        }
        actual_edge_widths = {
            tuple(flow["path"]): flow["payload"]["width"]
            for flow in his["data_flow"]
        }
        self.assertEqual(actual_edge_widths, expected_edge_widths)
        l0_result = check_project_l0(project)
        self.assertTrue(l0_result.passed, l0_result.errors)
        self.assertIn("TEST_PASS", _run_generated_testbench(project))

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_3a_sobel_threshold_four_frame_sequence_has_buffered_axis_contract_and_black_box_oracle(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="sobel_threshold", width=8, project_name="phase_b_3a_sobel_threshold"),
            platform,
        )

        his = _system_his(project)
        manifest = _manifest(project)
        self.assertEqual(his["architecture"]["task_family_id"], "sobel_threshold")
        self.assertEqual(
            set(manifest["sources"]),
            {
                "rtl/top.v",
                "rtl/sobel_line_buffer.v",
                "rtl/sobel_window.v",
                "rtl/sobel_threshold_core.v",
            },
        )
        ports = {port["name"] for port in _top_ports_from_interface(his["interface"])}
        self.assertEqual(
            ports,
            {
                "clk",
                "rst_n",
                "in_valid",
                "in_ready",
                "in_pixel",
                "in_last",
                "out_valid",
                "out_ready",
                "out_edge",
                "edge_axis",
                "out_last",
            },
        )
        self.assertEqual(
            {parameter["name"] for parameter in his["top"]["parameters"]},
            {"IMAGE_WIDTH", "IMAGE_HEIGHT", "THRESHOLD"},
        )
        self.assertIn("edge_axis_semantics", his["architecture"]["obligations"])
        self.assertIn("axis_sensitive_edges", his["verification"]["scenarios"])
        self.assertIn("stall_stability", his["verification"]["scenarios"])
        self.assertIn("parameter IMAGE_WIDTH = 5", project.files["rtl/top.v"])
        self.assertIn("parameter IMAGE_HEIGHT = 5", project.files["rtl/top.v"])
        self.assertIn("parameter THRESHOLD = 100", project.files["rtl/top.v"])
        self.assertIn("sobel_line_buffer", project.files["rtl/sobel_window.v"])
        self.assertIn("abs_gx >= abs_gy", project.files["rtl/sobel_threshold_core.v"])
        self.assertNotRegex(project.files["sim/tb_top.v"], r"\bdut\.")
        self.assertIn("vertical edge", project.files["sim/tb_top.v"].lower())
        self.assertIn("horizontal edge", project.files["sim/tb_top.v"].lower())
        l0_result = check_project_l0(project)
        self.assertTrue(l0_result.passed, l0_result.errors)
        self.assertIn("TEST_PASS", _run_generated_testbench(project))

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_3a_sobel_width9_addressing_and_final_in_last_are_black_box_safe(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="sobel_threshold", width=8, project_name="phase_b_3a_sobel_width9"),
            platform,
        )

        line_buffer = project.files["rtl/sobel_line_buffer.v"]
        window = project.files["rtl/sobel_window.v"]
        self.assertIn("parameter ADDR_WIDTH = (IMAGE_WIDTH <= 1) ? 1 : $clog2(IMAGE_WIDTH)", line_buffer)
        self.assertIn("parameter ADDR_WIDTH = (IMAGE_WIDTH <= 1) ? 1 : $clog2(IMAGE_WIDTH)", window)
        self.assertIn("final_input_last", project.files["rtl/top.v"])
        self.assertIn("frame_end_hold", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", _run_project_with_testbench(project, _sobel_width9_in_last_testbench()))

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_3b_vision_defect_core_reports_first_thresholded_pixel_without_bbox_claims(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="vision_defect_core", width=8, project_name="phase_b_3b_vision_defect"),
            platform,
        )

        his = _system_his(project)
        self.assertEqual(his["architecture"]["task_family_id"], "p_vision_defect_core")
        self.assertEqual(
            set(_manifest(project)["sources"]),
            {
                "rtl/top.v",
                "rtl/sobel_line_buffer.v",
                "rtl/sobel_window.v",
                "rtl/sobel_threshold_core.v",
                "rtl/vision_defect_accumulator.v",
                "rtl/vision_io_control.v",
            },
        )
        self.assertEqual(
            {parameter["name"] for parameter in his["top"]["parameters"]},
            {"IMAGE_WIDTH", "IMAGE_HEIGHT", "THRESHOLD"},
        )
        self.assertIn("bounded_first_defect_coordinate", his["architecture"]["obligations"])
        self.assertNotIn("bounding_box", " ".join(his["architecture"]["obligations"]).lower())
        self.assertNotIn("connected_component", json.dumps(his).lower())
        self.assertIn("out_last", project.files["rtl/top.v"])
        self.assertIn("defect_present", project.files["rtl/top.v"])
        self.assertIn("first_defect_x", project.files["rtl/top.v"])
        self.assertIn("first_defect_y", project.files["rtl/top.v"])
        self.assertNotRegex(project.files["sim/tb_top.v"], r"\bdut\.")
        data_paths = {tuple(flow["path"]) for flow in his["data_flow"]}
        self.assertIn(("top.in_pixel", "u_sobel_window.in_pixel"), data_paths)
        self.assertIn(("top.out_edge", "u_vision_defect_accumulator.pixel_edge"), data_paths)
        self.assertIn(("u_vision_defect_accumulator.defect_present", "top.defect_present"), data_paths)
        self.assertNotIn(("top.in_valid", "u_sobel_window.accept"), data_paths)
        self.assertNotIn(("top.out_valid", "u_vision_defect_accumulator.pixel_accept"), data_paths)
        control_flow = {rule["name"]: rule for rule in his["control_flow"]}
        self.assertEqual(control_flow["accepted_input_to_window"]["condition"], "top.in_valid && top.in_ready")
        self.assertEqual(control_flow["registered_output_accept"]["condition"], "top.out_valid && top.out_ready")
        self.assertIn("registered top.out_edge and top.out_last", control_flow["registered_output_accept"]["effects"][0])
        self.assertEqual(control_flow["out_last_report_select"]["condition"], "top.out_valid && top.out_last")
        self.assertIn("accumulator current values", control_flow["out_last_report_select"]["effects"][0])
        self.assertIn("TEST_PASS", _run_generated_testbench(project))

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_4_pattern_matcher_and_trigger_filter_have_four_token_backpressure_contracts(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        expected = {
            "pattern_matcher": {
                "family_id": "pattern_matcher",
                "sources": {"rtl/top.v", "rtl/pattern_matcher.v"},
                "modules": {"pattern_matcher"},
                "instances": {"u_pattern_matcher"},
            },
            "stream_trigger_filter": {
                "family_id": "p_stream_trigger_filter",
                "sources": {"rtl/top.v", "rtl/pattern_matcher.v", "rtl/trigger_fsm.v", "rtl/stream_packer.v"},
                "modules": {"pattern_matcher", "trigger_fsm", "stream_packer"},
                "instances": {"u_pattern_matcher", "u_trigger_fsm", "u_stream_packer"},
            },
        }

        for task_type, contract in expected.items():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_4_{task_type}"),
                    platform,
                )
                his = _system_his(project)
                self.assertEqual(his["architecture"]["task_family_id"], contract["family_id"])
                self.assertEqual(set(_manifest(project)["sources"]), contract["sources"])
                self.assertEqual(set(his["architecture"]["submodules"]), contract["modules"])
                instance_names = {instance["name"] for instance in his["instances"]}
                self.assertEqual(instance_names, contract["instances"])
                for flow in his["data_flow"]:
                    for endpoint in flow["path"]:
                        owner = endpoint.split(".", 1)[0]
                        if owner != "top":
                            self.assertIn(owner, instance_names)
                self.assertEqual(
                    {parameter["name"] for parameter in his["top"]["parameters"]},
                    {"TOKEN0", "TOKEN1", "TOKEN2", "TOKEN3"},
                )
                port_widths = {port["name"]: port["width"] for port in _top_ports_from_interface(his["interface"])}
                self.assertEqual(port_widths["in_data"], 8)
                self.assertEqual(port_widths["out_valid"], 1)
                self.assertEqual(port_widths["out_ready"], 1)
                self.assertEqual(port_widths["out_match_index"], 32)
                self.assertEqual(port_widths["out_match_word"], 32)
                self.assertIn("accepted-token index", his["verification"]["expected_behavior"])
                self.assertIn("overlapping_match", his["verification"]["scenarios"])
                self.assertIn("stall_stability", his["verification"]["scenarios"])
                self.assertNotRegex(project.files["sim/tb_top.v"], r"\bdut\.")
                self.assertIn("expect_held_match(32'd6", project.files["sim/tb_top.v"])
                self.assertIn("TEST_PASS", _run_generated_testbench(project))


def _task_type(project) -> str:
    return json.loads(project.files["system_his.json"])["task_type"]


def _manifest(project) -> dict:
    return json.loads(project.files["manifest.json"])


def _system_his(project) -> dict:
    return json.loads(project.files["system_his.json"])


def _predicted_resources(project) -> dict:
    predicted = json.loads(project.files["reports/predicted_qor.json"])["predicted"]
    return {key: predicted[key] for key in ("lut", "ff", "bram", "dsp")}


def _run_generated_testbench(project) -> str:
    manifest = _manifest(project)
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _write_project(project_dir, project)
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
        if compile_result.returncode != 0:
            raise AssertionError(compile_result.stdout + compile_result.stderr)
        run_result = subprocess.run(
            ["vvp", "sim.out"],
            cwd=project_dir,
            text=True,
            capture_output=True,
            check=False,
            timeout=3,
        )
    if run_result.returncode != 0:
        raise AssertionError(run_result.stdout + run_result.stderr)
    return run_result.stdout


def _run_project_with_testbench(project, testbench: str) -> str:
    manifest = _manifest(project)
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _write_project(project_dir, project)
        testbench_path = project_dir / manifest["simulation"]["testbench"]
        testbench_path.write_text(testbench, encoding="utf-8")
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
        if compile_result.returncode != 0:
            raise AssertionError(compile_result.stdout + compile_result.stderr)
        run_result = subprocess.run(
            ["vvp", "sim.out"],
            cwd=project_dir,
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    if run_result.returncode != 0:
        raise AssertionError(run_result.stdout + run_result.stderr)
    return run_result.stdout


def _sobel_width9_in_last_testbench() -> str:
    return r'''`timescale 1ns/1ps
module tb_top;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg in_valid = 1'b0;
  wire in_ready;
  reg [7:0] in_pixel = 8'd0;
  reg in_last = 1'b0;
  wire out_valid;
  reg out_ready = 1'b1;
  wire out_edge;
  wire edge_axis;
  wire out_last;
  integer output_count;
  reg saw_last;
  integer i;

  top #(.IMAGE_WIDTH(9), .IMAGE_HEIGHT(5), .THRESHOLD(100)) dut (
    .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready),
    .in_pixel(in_pixel), .in_last(in_last), .out_valid(out_valid),
    .out_ready(out_ready), .out_edge(out_edge), .edge_axis(edge_axis), .out_last(out_last)
  );

  always #5 clk = ~clk;

  always @(posedge clk) begin
    if (!rst_n) begin
      output_count <= 0;
      saw_last <= 1'b0;
    end else if (out_valid && out_ready) begin
      output_count <= output_count + 1;
      if (out_last)
        saw_last <= 1'b1;
    end
  end

  task apply_reset;
    begin
      @(negedge clk);
      rst_n = 1'b0;
      in_valid = 1'b0;
      in_last = 1'b0;
      repeat (2) @(posedge clk);
      @(negedge clk);
      rst_n = 1'b1;
    end
  endtask

  task send_pixel;
    input last_pixel;
    begin
      @(negedge clk);
      in_pixel = 8'd0;
      in_last = last_pixel;
      in_valid = 1'b1;
      while (!(in_valid && in_ready))
        @(posedge clk);
      @(negedge clk);
      in_valid = 1'b0;
      in_last = 1'b0;
    end
  endtask

  task send_frame;
    input final_last;
    begin
      for (i = 0; i < 45; i = i + 1)
        send_pixel(final_last && (i == 44));
    end
  endtask

  task wait_for_last;
    integer cycles;
    begin
      cycles = 0;
      while (!saw_last && (cycles < 600)) begin
        @(posedge clk);
        cycles = cycles + 1;
      end
      if (!saw_last) begin
        $display("ERROR missing out_last count=%0d", output_count);
        $fatal(1);
      end
      if (output_count != 45) begin
        $display("ERROR expected 45 outputs got %0d", output_count);
        $fatal(1);
      end
    end
  endtask

  initial begin
    apply_reset();
    send_frame(1'b1);
    wait_for_last();

    apply_reset();
    send_frame(1'b0);
    repeat (120) @(posedge clk);
    if (saw_last) begin
      $display("ERROR out_last emitted without final in_last");
      $fatal(1);
    end

    apply_reset();
    send_frame(1'b1);
    wait_for_last();
    $display("TEST_PASS");
    $finish;
  end
endmodule
'''


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
