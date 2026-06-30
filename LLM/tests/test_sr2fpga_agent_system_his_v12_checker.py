import copy
import json
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0
from LLM.src.sr2fpga_agent.system_his_v12_checker import (
    SCHEMA_VERSION,
    check_system_his_v12,
    check_system_his_v12_against_rtl,
)


FIXTURE = Path("docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json")


class SystemHisV12CheckerTest(unittest.TestCase):
    def test_canonical_schema_version_is_v12(self) -> None:
        self.assertEqual(SCHEMA_VERSION, "system-his-v1.2")

    def test_rejects_retired_topdown_schema_suffix(self) -> None:
        payload = _fixture()
        payload["schema_version"] = "system-his-v1.2-topdown"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("system_his.schema_version must be system-his-v1.2", result.errors)

    def test_accepts_t4_topdown_example(self) -> None:
        result = check_system_his_v12(_fixture())

        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.errors, [])

    def test_rejects_instance_that_references_missing_component(self) -> None:
        payload = _fixture()
        payload["instances"][0]["component"] = "missing_component"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("instances[0] references missing component 'missing_component'", result.errors)

    def test_rejects_verilog_reserved_instance_name(self) -> None:
        payload = _fixture()
        payload["instances"][2]["name"] = "join"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("instances[2].name 'join' is a Verilog reserved keyword", result.errors)

    def test_rejects_verilog_gate_primitive_instance_name(self) -> None:
        payload = _fixture()
        payload["instances"][2]["name"] = "buf"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("instances[2].name 'buf' is a Verilog reserved keyword", result.errors)

    def test_rejects_component_source_not_declared_in_artifacts(self) -> None:
        payload = _fixture()
        payload["components"][0]["source"] = "library"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("components[0].source 'library' is not in artifacts.rtl_sources", result.errors)

    def test_duplicate_component_does_not_clobber_original_ports(self) -> None:
        payload = _fixture()
        payload["components"].append(
            {
                "name": "skid_buffer",
                "semantic_kind": "stream_buffer",
                "source": "rtl/skid_buffer_dup.v",
                "parameters": [{"name": "DATA_WIDTH", "default": 8}],
                "ports": [
                    {"name": "clk", "dir": "input", "width": 1},
                    {"name": "rst_n", "dir": "input", "width": 1},
                ],
                "intent": "duplicate component definition with fewer ports",
            }
        )
        payload["artifacts"]["rtl_sources"].append("rtl/skid_buffer_dup.v")

        result = check_system_his_v12(payload)

        self.assertTrue(any("duplicate component 'skid_buffer'" in error for error in result.errors), result.errors)
        self.assertFalse(
            any("in0_buffer.in_data" in error or "in0_buffer.out_data" in error for error in result.errors),
            f"Duplicate component clobbered original port map: {result.errors}",
        )

    def test_rejects_data_flow_endpoint_that_uses_component_instead_of_instance(self) -> None:
        payload = _fixture()
        payload["data_flow"][0]["path"][1] = "skid_buffer.in_data"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn(
            "data_flow 'input0_payload_to_join' endpoint 'skid_buffer.in_data' is not a valid top or instance port",
            result.errors,
        )

    def test_data_flow_timing_is_optional_but_validated_when_present(self) -> None:
        self.assertTrue(check_system_his_v12(_fixture()).passed)
        payload = _fixture()
        payload["data_flow"][0]["timing"] = {
            "latency_cycles": 3,
            "initiation_interval": 0,
            "throughput": "",
        }

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("data_flow 'input0_payload_to_join'.timing.initiation_interval must be a positive integer", result.errors)
        self.assertIn("data_flow 'input0_payload_to_join'.timing.throughput must be a non-empty string", result.errors)

    def test_rejects_missing_intent_timing_resource_and_verification_details(self) -> None:
        payload = _fixture()
        payload["intent"]["design_goal"] = ""
        payload["top"]["clocks"] = [{"name": "", "target_fmax_mhz": 0}]
        payload["top"]["resets"] = [{"name": "rst_n", "polarity": "lowish", "kind": "maybe_sync"}]
        payload["timing"] = {"primary_clock": "", "target_fmax_mhz": 0, "constraints": []}
        payload["resources"] = {"optimization_goal": "", "expected": "low"}
        payload["verification"] = {"testbench": "", "scenarios": "reset", "pass_condition": ""}

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("system_his.intent.design_goal is required", result.errors)
        self.assertIn("system_his.top.clocks[0].name is required", result.errors)
        self.assertIn("system_his.top.clocks[0].target_fmax_mhz must be positive", result.errors)
        self.assertIn("system_his.top.resets[0].polarity is invalid", result.errors)
        self.assertIn("system_his.top.resets[0].kind is invalid", result.errors)
        self.assertIn("system_his.timing.primary_clock is required", result.errors)
        self.assertIn("system_his.timing.target_fmax_mhz must be positive", result.errors)
        self.assertIn("system_his.resources.optimization_goal is required", result.errors)
        self.assertIn("system_his.resources.expected must be an object", result.errors)
        self.assertIn("system_his.verification.testbench is required", result.errors)
        self.assertIn("system_his.verification.scenarios must be a list", result.errors)
        self.assertIn("system_his.verification.pass_condition is required", result.errors)

    def test_rejects_missing_component_instance_flow_and_control_contract_details(self) -> None:
        payload = _fixture()
        payload["components"][0]["semantic_kind"] = ""
        payload["components"][0]["source"] = ""
        payload["components"][0]["intent"] = ""
        payload["instances"][0]["clock"] = ""
        payload["instances"][0]["reset"] = ""
        payload["instances"][0]["parameter_values"] = "none"
        payload["data_flow"][0]["protocol"] = ""
        payload["data_flow"][0]["payload"] = "byte"
        payload["control_flow"][0]["kind"] = "free_text_rule"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("components[0].semantic_kind is required", result.errors)
        self.assertIn("components[0].source is required", result.errors)
        self.assertIn("components[0].intent is required", result.errors)
        self.assertIn("instances[0].clock is required", result.errors)
        self.assertIn("instances[0].reset is required", result.errors)
        self.assertIn("instances[0].parameter_values must be an object", result.errors)
        self.assertIn("data_flow 'input0_payload_to_join'.protocol is required", result.errors)
        self.assertIn("data_flow 'input0_payload_to_join'.payload must be an object", result.errors)
        self.assertIn("control_flow 'reset_all_state'.kind 'free_text_rule' is invalid", result.errors)

    def test_rejects_instance_parameter_value_not_declared_by_component(self) -> None:
        payload, _ = _consistent_v12_project()
        payload["instances"][0]["parameter_values"] = {"DATA_WIDTH": 8}

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn(
            "instances[0].parameter_values.DATA_WIDTH is not declared by component 'counter_core'",
            result.errors,
        )

        payload["components"][0]["parameters"] = [{"name": "DATA_WIDTH", "default": 8, "type": "integer"}]

        result = check_system_his_v12(payload)

        self.assertTrue(result.passed, result.errors)

    def test_rejects_control_rule_references_to_missing_state_and_flow(self) -> None:
        payload = _fixture()
        payload["control_flow"][0]["related_state"].append("missing_state")
        payload["control_flow"][0]["related_flows"].append("missing_flow")

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("control_flow 'reset_all_state' references missing state 'missing_state'", result.errors)
        self.assertIn("control_flow 'reset_all_state' references missing data_flow 'missing_flow'", result.errors)

    def test_accepts_declared_reset_as_control_guard_when_not_repeated_in_top_ports(self) -> None:
        payload = _fixture()
        payload["top"]["ports"] = [port for port in payload["top"]["ports"] if port["name"] != "rst_n"]
        payload["control_flow"].append(
            {
                "name": "reset_accum",
                "kind": "reset_rule",
                "when": {"signal": "top.rst_n", "op": "==", "value": 0},
                "effect": {"action": "clear", "target": "sum_q"},
                "related_state": ["sum_q"],
                "related_flows": [],
            }
        )

        result = check_system_his_v12(payload)

        self.assertTrue(result.passed, result.errors)

    def test_rejects_fsm_initial_state_outside_declared_states(self) -> None:
        payload = _fixture_with_fsm({"initial": "BROKEN"})

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("state.fsms 'join_fsm'.initial 'BROKEN' is not declared in states", result.errors)

    def test_rejects_fsm_without_explicit_or_instance_prefixed_owner(self) -> None:
        payload = _fixture()
        del payload["state"]["fsms"][0]["owner"]

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("state.fsms 'join_fsm' must declare owner or use <instance>.<fsm> name", result.errors)

    def test_rejects_fsm_owner_that_is_not_top_or_instance(self) -> None:
        payload = _fixture()
        payload["state"]["fsms"][0]["owner"] = "missing_instance"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("state.fsms 'join_fsm'.owner 'missing_instance' is not top or an instance", result.errors)

    def test_fsm_owner_top_valid_when_top_name_absent(self) -> None:
        payload = _fixture()
        payload["top"].pop("name", None)
        payload["state"]["fsms"].append(
            {
                "owner": "top",
                "name": "ctrl_fsm",
                "states": ["IDLE", "RUN"],
                "initial": "IDLE",
                "reset_state": "IDLE",
                "transitions": [],
            }
        )

        result = check_system_his_v12(payload)

        self.assertNotIn("state.fsms 'ctrl_fsm'.owner 'top' is not top or an instance", result.errors)

    def test_rejects_fsm_transition_to_missing_state(self) -> None:
        payload = _fixture_with_fsm()
        payload["control_flow"].append(
            {
                "name": "bad_transition",
                "kind": "fsm_transition",
                "fsm": "join_fsm",
                "from": "IDLE",
                "to": "MISSING",
                "when": {"signal": "top.in0_valid", "op": "==", "value": 1},
                "related_state": ["join_fsm.state"],
                "related_flows": [],
            }
        )

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("control_flow 'bad_transition'.to 'MISSING' is not a state of FSM 'join_fsm'", result.errors)

    def test_rejects_guard_nesting_deeper_than_two(self) -> None:
        payload = _fixture_with_fsm()
        payload["control_flow"].append(
            {
                "name": "too_deep_guard",
                "kind": "enable_rule",
                "when": {
                    "all_of": [
                        {
                            "any_of": [
                                {"all_of": [{"signal": "top.in0_valid", "op": "==", "value": 1}]}
                            ]
                        }
                    ]
                },
                "effect": {"action": "assert", "target": "input0_payload_to_join"},
                "related_state": ["join_fsm.state"],
                "related_flows": ["input0_payload_to_join"],
            }
        )

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertTrue(any("guard nesting depth" in error for error in result.errors), result.errors)

    def test_rejects_guard_unknown_operator(self) -> None:
        payload = _fixture_with_fsm()
        payload["control_flow"].append(
            {
                "name": "unknown_guard_op",
                "kind": "enable_rule",
                "when": {"signal": "top.in0_valid", "op": "~=", "value": 1},
                "effect": {"action": "assert", "target": "input0_payload_to_join"},
                "related_state": ["join_fsm.state"],
                "related_flows": ["input0_payload_to_join"],
            }
        )

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("control_flow 'unknown_guard_op'.when operator '~=' is not allowed", result.errors)

    def test_rejects_structured_effect_missing_flow_for_handshake_rule(self) -> None:
        payload = _fixture()
        payload["control_flow"].append(
            {
                "name": "bad_handshake_effect",
                "kind": "handshake_rule",
                "when": {"signal": "top.in0_valid", "op": "==", "value": 1},
                "effect": {"action": "assert", "target": "missing_flow"},
                "related_state": ["join_fsm.state"],
                "related_flows": [],
            }
        )

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("control_flow 'bad_handshake_effect'.effect.target 'missing_flow' is not declared", result.errors)

    def test_accepts_owner_qualified_state_references(self) -> None:
        payload = _fixture()
        payload["state"]["buffers"][0]["name"] = "skid_register"
        payload["state"]["buffers"][0]["owner"] = "in0_buffer"
        payload["instances"][0]["owns_state"] = ["in0_buffer.skid_register"]
        payload["control_flow"][0]["related_state"][0] = "in0_buffer.skid_register"
        payload["control_flow"][1]["related_state"][0] = "in0_buffer.skid_register"

        result = check_system_his_v12(payload)

        self.assertTrue(result.passed, result.errors)

    def test_rejects_missing_required_sections(self) -> None:
        payload = _fixture()
        del payload["top"]

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("system_his.top is required", result.errors)

    def test_cross_check_passes_for_consistent_project(self) -> None:
        payload, project = _consistent_v12_project()

        result = check_system_his_v12_against_rtl(payload, project)

        self.assertTrue(result.passed, result.errors)

    def test_cross_check_flags_renamed_component_port(self) -> None:
        payload, project = _consistent_v12_project()
        files = dict(project.files)
        files["rtl/counter_core.v"] = files["rtl/counter_core.v"].replace("output reg [7:0] count", "output reg [7:0] cnt")
        broken = GeneratedProject(project_name=project.project_name, files=files)

        result = check_system_his_v12_against_rtl(payload, broken)

        self.assertFalse(result.passed)
        self.assertIn("component 'counter_core' port 'count' is not declared in RTL", result.errors)

    def test_cross_check_flags_direction_mismatch(self) -> None:
        payload, project = _consistent_v12_project()
        files = dict(project.files)
        files["rtl/counter_core.v"] = files["rtl/counter_core.v"].replace("output reg [7:0] count", "input [7:0] count")
        broken = GeneratedProject(project_name=project.project_name, files=files)

        result = check_system_his_v12_against_rtl(payload, broken)

        self.assertFalse(result.passed)
        self.assertIn("component 'counter_core' port 'count' direction 'output' does not match RTL 'input'", result.errors)

    def test_cross_check_treats_numeric_width_and_range_as_equivalent(self) -> None:
        payload, project = _consistent_v12_project()
        payload["components"][0]["ports"][3]["width"] = "8"

        result = check_system_his_v12_against_rtl(payload, project)

        self.assertTrue(result.passed, result.errors)

    def test_cross_check_treats_his_width_expr_as_equivalent_to_parameterized_range(self) -> None:
        payload, project = _consistent_v12_project()
        payload["top"]["parameters"] = [{"name": "DATA_WIDTH", "default": 8, "type": "integer"}]
        payload["top"]["ports"][3]["width"] = {"expr": "[DATA_WIDTH-1:0]", "resolved": 8}
        payload["components"][0]["ports"][3]["width"] = {"expr": "[DATA_WIDTH-1:0]", "resolved": 8}
        files = dict(project.files)
        files["rtl/top.v"] = (
            "module top #(parameter DATA_WIDTH = 8)(input clk, input rst_n, input en, "
            "output [DATA_WIDTH-1:0] count);\n"
            "  counter_core #(.DATA_WIDTH(DATA_WIDTH)) u_counter(.clk(clk), .rst_n(rst_n), .en(en), .count(count));\n"
            "endmodule\n"
        )
        files["rtl/counter_core.v"] = (
            "module counter_core #(parameter DATA_WIDTH = 8)(input clk, input rst_n, input en, "
            "output reg [DATA_WIDTH-1:0] count);\n"
            "  always @(posedge clk) begin\n"
            "    if (!rst_n) count <= {DATA_WIDTH{1'b0}};\n"
            "    else if (en) count <= count + {{(DATA_WIDTH-1){1'b0}}, 1'b1};\n"
            "  end\n"
            "endmodule\n"
        )
        parameterized = GeneratedProject(project_name=project.project_name, files=files)

        result = check_system_his_v12_against_rtl(payload, parameterized)

        self.assertTrue(result.passed, result.errors)

    def test_cross_check_treats_his_width_resolved_as_equivalent_to_concrete_rtl_width(self) -> None:
        payload, project = _consistent_v12_project()
        payload["top"]["parameters"] = [{"name": "DATA_WIDTH", "default": 8, "type": "integer"}]
        payload["top"]["ports"][3]["width"] = {"expr": "DATA_WIDTH", "resolved": 8}
        payload["components"][0]["ports"][3]["width"] = {"expr": "DATA_WIDTH", "resolved": 8}

        result = check_system_his_v12_against_rtl(payload, project)

        self.assertTrue(result.passed, result.errors)

    def test_l0_dispatch_runs_v12_cross_check_on_v12_project(self) -> None:
        _, project = _consistent_v12_project()
        files = dict(project.files)
        files["sim/tb_top.v"] = "module tb; wrong_top dut(); endmodule\n"
        broken = GeneratedProject(project_name=project.project_name, files=files)

        result = check_project_l0(broken)

        self.assertFalse(result.passed)
        self.assertIn("manifest testbench 'sim/tb_top.v' does not instantiate top module 'top'", result.errors)

    def test_cross_check_infers_fsm_owner_from_instance_prefixed_name(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="composed_dual_stream_join", width=8, project_name="join_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        payload = json.loads(project.files["system_his.json"])
        payload["state"]["fsms"].append(
            {
                "name": "u_stream_join.arb_fsm",
                "states": ["IDLE", "SEND_0", "SEND_1"],
                "initial": "IDLE",
                "reset_state": "IDLE",
            }
        )
        for instance in payload["instances"]:
            if instance["name"] == "u_stream_join":
                instance["owns_state"] = ["u_stream_join.arb_fsm"]
        files = dict(project.files)
        files["system_his.json"] = json.dumps(payload) + "\n"
        files["rtl/stream_join.v"] = files["rtl/stream_join.v"].replace(
            "endmodule\n",
            "  localparam IDLE = 0;\n  localparam SEND_0 = 1;\n  localparam SEND_1 = 2;\nendmodule\n",
        )
        project_with_fsm = GeneratedProject(project_name=project.project_name, files=files)

        result = check_project_l0(project_with_fsm)

        self.assertTrue(result.passed, result.errors)


def _fixture() -> dict[str, object]:
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _fixture_with_fsm(overrides: dict[str, object] | None = None) -> dict[str, object]:
    payload = _fixture()
    fsm = {
        "name": "join_fsm",
        "owner": "join_core",
        "states": ["IDLE", "WAIT_BOTH", "FIRE"],
        "initial": "IDLE",
        "reset_state": "IDLE",
    }
    if overrides:
        fsm.update(overrides)
    payload["state"]["fsms"].append(fsm)
    return payload


def _consistent_v12_project() -> tuple[dict[str, object], GeneratedProject]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "intent": {"user_prompt": "Build an 8-bit counter.", "design_goal": "Counter project.", "assumptions": []},
        "top": {
            "name": "top",
            "parameters": [],
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [{"name": "rst_n", "polarity": "active_low", "kind": "sync"}],
            "ports": [
                {"name": "clk", "dir": "input", "width": 1},
                {"name": "rst_n", "dir": "input", "width": 1},
                {"name": "en", "dir": "input", "width": 1},
                {"name": "count", "dir": "output", "width": 8},
            ],
            "interfaces": [],
        },
        "state": {
            "registers": [{"name": "count_q", "owner": "u_counter", "width": 8}],
            "counters": [],
            "fsms": [],
            "buffers": [],
            "memories": [],
        },
        "components": [
            {
                "name": "counter_core",
                "semantic_kind": "counter",
                "source": "rtl/counter_core.v",
                "parameters": [],
                "ports": [
                    {"name": "clk", "dir": "input", "width": 1},
                    {"name": "rst_n", "dir": "input", "width": 1},
                    {"name": "en", "dir": "input", "width": 1},
                    {"name": "count", "dir": "output", "width": 8},
                ],
                "intent": "8-bit counter datapath and state update logic",
            }
        ],
        "instances": [
            {
                "name": "u_counter",
                "component": "counter_core",
                "parameter_values": {},
                "clock": "clk",
                "reset": "rst_n",
                "owns_state": ["u_counter.count_q"],
            }
        ],
        "data_flow": [
            {
                "name": "count_path",
                "path": ["top.en", "u_counter.en", "u_counter.count", "top.count"],
                "payload": {"name": "count_value", "width": 8},
                "protocol": "register",
            }
        ],
        "control_flow": [
            {
                "name": "increment_when_enabled",
                "kind": "enable_rule",
                "condition": "en",
                "effects": ["count_q := count_q + 1"],
                "related_state": ["u_counter.count_q"],
                "related_flows": ["count_path"],
            }
        ],
        "timing": {"primary_clock": "clk", "target_fmax_mhz": 100, "constraints": ["constraints/timing.sdc"]},
        "resources": {"optimization_goal": "area_first", "expected": {"lut": "low", "ff": "low", "bram": 0, "dsp": 0}},
        "verification": {"testbench": "sim/tb_top.v", "scenarios": [], "pass_condition": "TEST_PASS"},
        "artifacts": {
            "top_module": "top",
            "rtl_sources": ["rtl/top.v", "rtl/counter_core.v"],
            "testbench": "sim/tb_top.v",
            "constraints": ["constraints/timing.sdc"],
            "manifest": "manifest.json",
            "predicted_qor": "reports/predicted_qor.json",
        },
    }
    files = {
        "system_his.json": json.dumps(payload),
        "manifest.json": json.dumps(
            {
                "top_module": "top",
                "sources": ["rtl/top.v", "rtl/counter_core.v"],
                "simulation": {"testbench": "sim/tb_top.v"},
                "constraints": {"timing": "constraints/timing.sdc"},
            }
        ),
        "rtl/top.v": """
module top(input clk, input rst_n, input en, output [7:0] count);
  counter_core u_counter(.clk(clk), .rst_n(rst_n), .en(en), .count(count));
endmodule
""",
        "rtl/counter_core.v": """
module counter_core(input clk, input rst_n, input en, output reg [7:0] count);
  always @(posedge clk) begin
    if (!rst_n) count <= 8'd0;
    else if (en) count <= count + 8'd1;
  end
endmodule
""",
        "sim/tb_top.v": "module tb; reg clk, rst_n, en; wire [7:0] count; top dut(clk, rst_n, en, count); endmodule\n",
        "constraints/timing.sdc": "create_clock -period 10 [get_ports clk]\n",
        "reports/predicted_qor.json": "{}\n",
    }
    return payload, GeneratedProject(project_name="counter8", files=files)


if __name__ == "__main__":
    unittest.main()
