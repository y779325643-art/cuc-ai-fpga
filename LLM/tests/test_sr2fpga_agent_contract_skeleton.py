import json
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.contract_skeleton import build_contract_skeleton_project, merge_behavior_files
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12_against_rtl


FIXTURE = Path("docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json")


class ContractSkeletonTest(unittest.TestCase):
    def test_builds_l0_clean_project_skeleton_from_system_his_v12(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = build_contract_skeleton_project(request, platform, system_his)

        self.assertEqual(json.loads(project.files["system_his.json"]), system_his)
        manifest = json.loads(project.files["manifest.json"])
        self.assertEqual(manifest["sources"], system_his["artifacts"]["rtl_sources"])
        self.assertIn("rtl/top.v", project.files)
        self.assertIn("rtl/stream_join.v", project.files)
        self.assertIn("BEHAVIOR_HOLE", project.files["rtl/stream_join.v"])
        self.assertRegex(project.files["rtl/top.v"], r"\bstream_join\b\s*(?:#\s*\(.*?\)\s*)?join_core\s*\(")
        self.assertIn("top dut", project.files["sim/tb_top.v"])
        self.assertIn("[get_ports clk]", project.files["constraints/timing.sdc"])

        result = check_system_his_v12_against_rtl(system_his, project)

        self.assertTrue(result.passed, result.errors)

    def test_merges_behavior_files_without_allowing_structural_rewrites(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        skeleton = build_contract_skeleton_project(request, platform, system_his)

        project = merge_behavior_files(
            skeleton,
            {
                "rtl/skid_buffer.v": "// no behavior needed for this structural unit test",
                "rtl/stream_join.v": "assign out_valid = in0_valid && in1_valid;\nassign out_data = in0_data + in1_data;",
                "rtl/accumulator_core.v": "assign sample_ready = sum_ready;\nassign sum_valid = sample_valid;\nassign sum = sample;",
                "rtl/stream_stage.v": "// no behavior needed for this structural unit test",
            },
        )

        self.assertNotIn("BEHAVIOR_HOLE", project.files["rtl/stream_join.v"])
        self.assertIn("assign out_valid = in0_valid && in1_valid;", project.files["rtl/stream_join.v"])
        self.assertIn("module top", project.files["rtl/top.v"])
        self.assertEqual(project.files["manifest.json"], skeleton.files["manifest.json"])

        result = check_system_his_v12_against_rtl(system_his, project)

        self.assertTrue(result.passed, result.errors)

    def test_top_skeleton_materializes_data_flow_connections(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        top_rtl = skeleton.files["rtl/top.v"]
        self.assertIn("assign in0_buffer__in_data = in0_data;", top_rtl)
        self.assertIn("assign in0_buffer__in_valid = in0_valid;", top_rtl)
        self.assertIn("assign in0_ready = in0_buffer__in_ready;", top_rtl)
        self.assertIn("assign join_core__in0_data = in0_buffer__out_data;", top_rtl)
        self.assertIn("assign join_core__in0_valid = in0_buffer__out_valid;", top_rtl)
        self.assertIn("assign in0_buffer__out_ready = join_core__in0_ready;", top_rtl)
        self.assertIn("assign accumulator__sample = join_core__out_data;", top_rtl)
        self.assertIn("assign out_data = out_stage__out_data;", top_rtl)
        self.assertIn("assign out_valid = out_stage__out_valid;", top_rtl)
        self.assertIn("assign out_stage__out_ready = out_ready;", top_rtl)
        self.assertNotIn("assign in0_buffer__out_data = in0_buffer__in_data;", top_rtl)
        self.assertNotIn("assign out_stage__out_data = out_stage__in_data;", top_rtl)

    def test_top_skeleton_handles_data_flow_without_source_handshake_companions(self) -> None:
        system_his = _fixture()
        for component in system_his["components"]:
            if component["name"] == "accumulator_core":
                component["ports"] = [
                    port for port in component["ports"] if port["name"] not in {"sum_valid", "sum_ready"}
                ]
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        top_rtl = skeleton.files["rtl/top.v"]
        self.assertIn("assign out_stage__in_valid = 1'b1;", top_rtl)
        self.assertIn("wire _unused_data_flow_signals = &{1'b0, out_stage__in_ready};", top_rtl)

    def test_top_skeleton_wires_td_update_oracle_his_payload_edges(self) -> None:
        request = ProjectRequest(
            task_type="composed_td_update_core",
            width=8,
            project_name="td_update_8bit",
            description="Generate a TD update datapath.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        oracle_project = ProjectGenerator().generate(request, platform)
        system_his = json.loads(oracle_project.files["system_his.json"])

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        top_rtl = skeleton.files["rtl/top.v"]
        self.assertIn("assign u_td_input_stage__reward = reward;", top_rtl)
        self.assertIn("assign u_td_input_stage__value = value;", top_rtl)
        self.assertIn("assign u_td_update_core__discounted_return = u_discount_core__discounted_return;", top_rtl)
        self.assertIn("assign updated_value = u_stream_stage__updated_value_out;", top_rtl)
        self.assertIn("assign u_stream_stage__out_ready = out_ready;", top_rtl)
        self.assertIn("assign in_ready = u_td_input_stage__in_ready;", top_rtl)
        self.assertIn("assign u_td_input_stage__out_ready = u_discount_core__in_ready;", top_rtl)
        self.assertIn("assign u_discount_core__out_ready = u_td_update_core__in_ready;", top_rtl)
        self.assertIn("assign u_td_update_core__out_ready = u_stream_stage__in_ready;", top_rtl)
        self.assertNotIn("assign u_stream_stage__out_valid = out_valid;", top_rtl)
        self.assertIn(".SCALE_SHIFT(SCALE_SHIFT)", top_rtl)
        self.assertNotIn(".SCALE_SHIFT(4)", top_rtl)

    def test_td_update_skeleton_uses_independent_functional_testbench(self) -> None:
        request = ProjectRequest(
            task_type="composed_td_update_core",
            width=8,
            project_name="td_update_8bit",
            description="Generate a TD update datapath.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        oracle_project = ProjectGenerator().generate(request, platform)
        system_his = json.loads(oracle_project.files["system_his.json"])

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        testbench = skeleton.files["sim/tb_top.v"]
        self.assertIn("task send_update", testbench)
        self.assertIn("task expect_update", testbench)
        self.assertIn("TEST_FAIL", testbench)
        self.assertIn("td_error !== expected_error", testbench)
        self.assertIn("updated_value !== expected_value", testbench)
        self.assertLess(testbench.find("expect_update"), testbench.find('$display("TEST_PASS")'))

    def test_skeleton_testbench_fails_safe_without_functional_oracle(self) -> None:
        system_his = _fixture()
        system_his["task_type"] = "unsupported_contract_skeleton_task"
        request = ProjectRequest(
            task_type="unsupported_contract_skeleton_task",
            width=8,
            project_name="unsupported_8bit",
            description="Unsupported behavior should not get a fake passing testbench.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        testbench = skeleton.files["sim/tb_top.v"]
        self.assertIn("TEST_FAIL missing independent functional oracle", testbench)
        self.assertNotIn("TEST_PASS", testbench)

    def test_top_skeleton_replaces_default_valid_driver_with_explicit_flow(self) -> None:
        system_his = _fixture()
        for component in system_his["components"]:
            if component["name"] == "accumulator_core":
                component["ports"] = [
                    port for port in component["ports"] if port["name"] not in {"sum_valid", "sum_ready"}
                ]
        system_his["data_flow"].append(
            {
                "name": "valid_to_output_stage",
                "path": ["accumulator.sample_valid", "out_stage.in_valid"],
                "payload": {"name": "valid", "width": 1},
                "protocol": "valid_ready",
                "timing": {
                    "latency_cycles": 0,
                    "initiation_interval": 1,
                    "throughput": "valid follows accepted accumulator samples",
                },
            }
        )
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        top_rtl = skeleton.files["rtl/top.v"]
        self.assertIn("assign out_stage__in_valid = accumulator__sample_valid;", top_rtl)
        self.assertNotIn("assign out_stage__in_valid = 1'b1;", top_rtl)
        self.assertEqual(top_rtl.count("assign out_stage__in_valid ="), 1)

    def test_rejects_behavior_for_files_without_behavior_holes(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        skeleton = build_contract_skeleton_project(request, platform, system_his)

        with self.assertRaisesRegex(ValueError, "does not contain a BEHAVIOR_HOLE"):
            merge_behavior_files(skeleton, {"rtl/top.v": "module top; endmodule"})

    def test_rejects_missing_behavior_for_any_behavior_hole(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        skeleton = build_contract_skeleton_project(request, platform, system_his)

        with self.assertRaisesRegex(ValueError, "missing behavior for"):
            merge_behavior_files(skeleton, {"rtl/stream_join.v": "assign out_valid = in0_valid;"})

    def test_component_skeleton_infers_fsm_owner_from_instance_prefixed_name(self) -> None:
        system_his = _fixture()
        system_his["state"]["fsms"].append(
            {
                "name": "join_core.arb_fsm",
                "states": ["IDLE", "SEND_0", "SEND_1"],
                "initial": "IDLE",
                "reset_state": "IDLE",
            }
        )
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        self.assertIn("localparam SEND_0", skeleton.files["rtl/stream_join.v"])
        self.assertIn("localparam SEND_1", skeleton.files["rtl/stream_join.v"])
        self.assertIn(
            "wire _unused_fsm_states = &{1'b0, (IDLE == IDLE), (WAIT_BOTH == WAIT_BOTH), (FIRE == FIRE), (SEND_0 == SEND_0), (SEND_1 == SEND_1)};",
            skeleton.files["rtl/stream_join.v"],
        )

    def test_component_skeleton_consumes_optional_clock_reset_inputs(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        self.assertIn("wire _unused_clock_reset = &{1'b0, clk, rst_n};", skeleton.files["rtl/skid_buffer.v"])

    def test_testbench_materializes_parameterized_port_widths_in_functional_oracle(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        testbench = skeleton.files["sim/tb_top.v"]
        self.assertIn("reg [7:0] in0_data;", testbench)
        self.assertIn("reg [7:0] in1_data;", testbench)
        self.assertIn("wire [11:0] out_data;", testbench)
        self.assertIn("TEST_FAIL", testbench)

    def test_top_inherits_component_parameters_used_by_internal_wires(self) -> None:
        system_his = _fixture()
        system_his["top"]["parameters"] = []
        for component in system_his["components"]:
            component["parameters"] = [{"name": "DATA_WIDTH", "default": 8}]
            for port in component["ports"]:
                if port["name"].endswith("_data") or port["name"] in {"sample", "sum"}:
                    port["width"] = {"expr": "DATA_WIDTH", "resolved": 8}
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        self.assertIn("module top #(parameter DATA_WIDTH = 8)", skeleton.files["rtl/top.v"])

    def test_missing_or_null_width_defaults_to_scalar(self) -> None:
        system_his = _fixture()
        system_his["top"]["ports"][0].pop("width", None)
        system_his["components"][0]["ports"][0]["width"] = {"expr": None, "resolved": None}
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        self.assertNotIn("[None-1:0]", "\n".join(skeleton.files.values()))
        self.assertIn("input wire clk", skeleton.files["rtl/top.v"])
        self.assertIn("input wire clk", skeleton.files["rtl/skid_buffer.v"])

    def test_port_without_direction_defaults_to_input(self) -> None:
        system_his = {
            "schema_version": "system-his-v1.2",
            "intent": "test",
            "top": {
                "name": "top",
                "ports": [
                    {"name": "clk"},
                    {"name": "out", "dir": "output"},
                ],
                "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
                "resets": [],
            },
            "state": {"registers": [], "counters": [], "fsms": [], "buffers": [], "memories": []},
            "components": [],
            "instances": [],
            "data_flow": [],
            "control_flow": [],
            "timing": {"target_fmax_mhz": 100},
            "resources": {"optimization_goal": "area", "expected": {}},
            "verification": {"testbench": "tb_top", "scenarios": [], "pass_condition": "all_pass"},
            "artifacts": {"top_module": "top", "rtl_sources": ["rtl/top.v"]},
        }
        request = ProjectRequest(task_type="counter", width=8, project_name="p")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = build_contract_skeleton_project(request, platform, system_his)

        self.assertIn("input wire clk", project.files["rtl/top.v"])
        self.assertIn("output wire out", project.files["rtl/top.v"])

    def test_duplicate_component_source_raises(self) -> None:
        system_his = {
            "schema_version": "system-his-v1.2",
            "intent": "test",
            "top": {
                "name": "top",
                "ports": [],
                "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
                "resets": [],
            },
            "state": {"registers": [], "counters": [], "fsms": [], "buffers": [], "memories": []},
            "components": [
                {
                    "name": "a",
                    "semantic_kind": "logic",
                    "source": "rtl/shared.v",
                    "ports": [],
                    "intent": "first",
                },
                {
                    "name": "b",
                    "semantic_kind": "logic",
                    "source": "rtl/shared.v",
                    "ports": [],
                    "intent": "second",
                },
            ],
            "instances": [],
            "data_flow": [],
            "control_flow": [],
            "timing": {"target_fmax_mhz": 100},
            "resources": {"optimization_goal": "area", "expected": {}},
            "verification": {"testbench": "tb_top", "scenarios": [], "pass_condition": "all_pass"},
            "artifacts": {"top_module": "top", "rtl_sources": ["rtl/top.v", "rtl/shared.v"]},
        }
        request = ProjectRequest(task_type="counter", width=8, project_name="p")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with self.assertRaisesRegex(ValueError, "same source path"):
            build_contract_skeleton_project(request, platform, system_his)

    def test_merge_does_not_duplicate_fsm_localparams_from_behavior(self) -> None:
        system_his = _fixture()
        system_his["state"]["fsms"].append(
            {
                "name": "join_core.join_fsm",
                "states": ["IDLE", "WAIT", "JOINED"],
                "initial": "IDLE",
                "reset_state": "IDLE",
            }
        )
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        skeleton = build_contract_skeleton_project(request, platform, system_his)

        project = merge_behavior_files(
            skeleton,
            {
                "rtl/skid_buffer.v": "// no behavior needed for this structural unit test",
                "rtl/stream_join.v": "\n".join(
                    [
                        "localparam [1:0] IDLE = 2'd0;",
                        "localparam [1:0] WAIT = 2'd1;",
                        "localparam [1:0] JOINED = 2'd2;",
                        "assign out_valid = in0_valid && in1_valid;",
                        "assign out_data = in0_data;",
                    ]
                ),
                "rtl/accumulator_core.v": "assign sample_ready = sum_ready;\nassign sum_valid = sample_valid;\nassign sum = sample;",
                "rtl/stream_stage.v": "// no behavior needed for this structural unit test",
            },
        )

        stream_join = project.files["rtl/stream_join.v"]
        self.assertNotIn("localparam IDLE = 0;", stream_join)
        self.assertNotIn("localparam WAIT = 0;", stream_join)
        self.assertNotIn("localparam JOINED = 0;", stream_join)

    def test_merge_drops_duplicate_unused_clock_reset_from_behavior(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        skeleton = build_contract_skeleton_project(request, platform, system_his)

        project = merge_behavior_files(
            skeleton,
            {
                "rtl/skid_buffer.v": "wire _unused_clock_reset = &{1'b0, clk, rst_n};",
                "rtl/stream_join.v": "assign out_valid = in0_valid && in1_valid;",
                "rtl/accumulator_core.v": "assign sample_ready = sum_ready;\nassign sum_valid = sample_valid;",
                "rtl/stream_stage.v": "// no behavior needed for this structural unit test",
            },
        )

        self.assertEqual(project.files["rtl/skid_buffer.v"].count("_unused_clock_reset"), 1)

    def test_skeleton_preserves_complete_width_ranges(self) -> None:
        system_his = _fixture()
        for port in system_his["top"]["ports"]:
            if port["name"] in {"in0_data", "in1_data", "out_data"}:
                port["width"] = {"expr": "7:0", "resolved": 8}
        for component in system_his["components"]:
            for port in component["ports"]:
                if port["name"].endswith("_data") or port["name"] in {"sample", "sum"}:
                    port["width"] = {"expr": "DATA_WIDTH-1:0", "resolved": None}
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        skeleton = build_contract_skeleton_project(request, platform, system_his)

        self.assertNotIn("[7:0-1:0]", skeleton.files["rtl/top.v"])
        self.assertNotIn("[DATA_WIDTH-1:0-1:0]", "\n".join(skeleton.files.values()))
        self.assertIn("input wire [7:0] in0_data", skeleton.files["rtl/top.v"])
        self.assertIn("input wire [DATA_WIDTH-1:0] in_data", skeleton.files["rtl/skid_buffer.v"])
        result = check_system_his_v12_against_rtl(system_his, skeleton)
        self.assertTrue(result.passed, result.errors)


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
