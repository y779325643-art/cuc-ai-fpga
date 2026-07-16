"""Prompt construction helpers for SR2FPGA generation and repair."""

from __future__ import annotations

import json
from typing import Any

from LLM.src.sr2fpga_agent.contract_skeleton import (
    BEHAVIOR_REGION_BEGIN,
    BEHAVIOR_REGION_END,
    build_contract_skeleton_project,
)
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.parsers import (
    MULTIMODULE_RTL_EXAMPLES,
    REQUIRED_PROJECT_FILES,
    _project_system_his_schema,
    _project_task_type,
)
from LLM.src.sr2fpga_agent.system_his_v12_checker import SCHEMA_VERSION as SYSTEM_HIS_V12_SCHEMA

def _system_his_v12_messages(request: ProjectRequest, platform: PlatformProfile) -> list[dict[str, str]]:
    system = (
        "You are an FPGA system architect. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate RTL, testbench code, constraints, bitstreams, or tool reports."
    )
    user = f"""
Generate a canonical System-HIS v1.2 architecture contract for SR2FPGA.

Project:
- project_name: {request.project_name}
- task_type: {request.task_type}
- width: {request.width}
- user_prompt: {request.description or "No extra user prompt provided."}

Target platform:
- name: {platform.name}
- vendor: {platform.vendor}
- family: {platform.family}
- part: {platform.part}
- board: {platform.board}
- toolchain: {platform.toolchain}
- clock_hz: {platform.clock_hz}
- reset_polarity: {platform.reset_polarity}

Return only System-HIS JSON with schema_version "system-his-v1.2".
Do not generate RTL or project files in this step.

Required top-level sections:
- intent
- top
- state
- components
- instances
- data_flow
- control_flow
- timing
- resources
- verification
- artifacts

Architectural rules:
- Start from top-level ports, interfaces, clocks, resets, and parameters.
- Every clock and reset declared in top.clocks/top.resets must also appear in top.ports.
- top.resets[].polarity must be active_low or active_high.
- top.resets[].kind must be sync or async.
- Use {{"name": "rst_n", "polarity": "active_low", "kind": "sync"}} unless the task explicitly says otherwise.
- Record architectural state, not incidental RTL temporaries.
- State names across registers, counters, fsms, buffers, and memories must be globally unique.
- Separate component definitions from concrete instances.
- Every component must include name, semantic_kind, source, ports, and intent.
- Every components[].source must be one of artifacts.rtl_sources.
- Do not use placeholder sources such as "library"; use concrete RTL paths like rtl/top.v.
- Every instance must include name, component, parameter_values, clock, reset, and owns_state.
- Every instances[].owns_state must be a JSON array; use [] when the instance owns no state.
- Every instances[].parameter_values key must be declared in that component's parameters.
- top.clocks[].target_fmax_mhz and timing.target_fmax_mhz must be positive numbers.
- Every data_flow endpoint must name top.<port> or <instance>.<port>.
- data_flow.timing is optional, but when present it must include
  latency_cycles >= 0, initiation_interval > 0, and optional non-empty throughput.
- Separate data movement from control rules.
- control_flow rules should use kinds such as reset_rule, handshake_rule,
  enable_rule, stall_rule, counter_update, fsm_transition, or buffer_occupancy.
- Structured control_flow rules should use when/effect objects when modeling
  machine-checkable behavior. The guard grammar allows atoms {"signal","op","value"} or
  all_of/any_of lists with depth <= 2; signal must reference a declared top port,
  top clock/reset, instance port, state, data_flow name, or <fsm>.state.
- control_flow.effect.target must reference a declared data_flow name or state name; do not target
  top ports, instance ports, all, or module names directly.
- Every state.fsms[] entry must declare owner or use <instance>.<fsm> naming.
- FSM owner must be top or an instances[].name.
- fsm_transition rules must reference a declared state.fsms entry and use
  from/to states declared by that FSM.
- Use width objects with expr and resolved when a parameterized width is useful.
- Keep verification as scenarios and pass_condition, not full testbench code.

{_system_his_v12_task_guidance(request.task_type)}

Return this JSON shape:
{{
  "schema_version": "system-his-v1.2",
  "intent": {{
    "user_prompt": "...",
    "design_goal": "...",
    "assumptions": []
  }},
  "top": {{
    "name": "top",
    "parameters": [],
    "clocks": [],
    "resets": [],
    "ports": [],
    "interfaces": []
  }},
  "state": {{
    "registers": [],
    "counters": [],
    "fsms": [],
    "buffers": [],
    "memories": []
  }},
  "components": [],
  "instances": [],
  "data_flow": [
    {{
      "name": "...",
      "path": ["top.input_port", "instance.input_port", "instance.output_port", "top.output_port"],
      "payload": {{"name": "...", "width": {{"expr": "DATA_WIDTH", "resolved": 8}}}},
      "protocol": "valid_ready",
      "timing": {{"latency_cycles": 1, "initiation_interval": 1, "throughput": "one transfer per cycle when ready"}}
    }}
  ],
  "control_flow": [
    {{
      "name": "...",
      "kind": "enable_rule",
      "when": {{"signal": "top.valid", "op": "==", "value": 1}},
      "effect": {{"action": "assert", "target": "..."}},
      "related_state": [],
      "related_flows": []
    }}
  ],
  "timing": {{
    "primary_clock": "clk",
    "target_fmax_mhz": 100,
    "constraints": ["constraints/timing.sdc"]
  }},
  "resources": {{
    "optimization_goal": "area_first",
    "expected": {{"lut": "low", "ff": "low", "bram": 0, "dsp": 0}}
  }},
  "verification": {{
    "testbench": "sim/tb_top.v",
    "scenarios": [],
    "pass_condition": "testbench prints TEST_PASS and no TEST_FAIL"
  }},
  "artifacts": {{
    "top_module": "top",
    "rtl_sources": [],
    "testbench": "sim/tb_top.v",
    "constraints": ["constraints/timing.sdc"],
    "manifest": "manifest.json",
    "predicted_qor": "reports/predicted_qor.json"
  }}
}}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _with_system_his_retry_feedback(
    messages: list[dict[str, str]],
    error: str,
    previous_content: str,
    task_type: str = "",
) -> list[dict[str, str]]:
    task_guidance = _system_his_v12_retry_guidance(task_type)
    return [
        *messages,
        {"role": "assistant", "content": previous_content or "{}"},
        {
            "role": "user",
            "content": (
                "Your previous System-HIS output failed validation. "
                "Repair that JSON in place and return a corrected complete System-HIS JSON object only.\n\n"
                "Validation error:\n"
                f"{error}\n\n"
                "System-HIS v1.2 IR repair checklist:\n"
                "- Every components[] object must include name, semantic_kind, source, ports, and intent.\n"
                "- Every components[].source must be one of artifacts.rtl_sources.\n"
                "- Do not use placeholder sources such as \"library\"; use concrete RTL paths like rtl/top.v.\n"
                "- Every instances[] object must include name, component, parameter_values, clock, reset, and owns_state.\n"
                "- Every instances[].owns_state must be a JSON array; use [] when the instance owns no state.\n"
                "- Every instances[].parameter_values key must be declared in that component's parameters.\n"
                "- Every instance name must be unique and every component value must match a declared components[].name.\n"
                "- Every top clock/reset should be listed in top.clocks/top.resets and also in top.ports.\n"
                "- top.clocks[].target_fmax_mhz and timing.target_fmax_mhz must be positive numbers.\n"
                "- top.resets[].polarity must be active_low or active_high.\n"
                "- top.resets[].kind must be sync or async.\n"
                "- Use {\"name\": \"rst_n\", \"polarity\": \"active_low\", \"kind\": \"sync\"} unless the task "
                "explicitly says otherwise.\n"
                "- data_flow.path endpoints must use top.<port> or <instance>.<port>; do not use component names as endpoints.\n"
                "- control_flow.when signal values must reference declared top ports, instance ports, state names, "
                "data_flow names, or <fsm>.state.\n"
                "- control_flow.effect.target must reference a declared data_flow name or state name; do not target "
                "top ports, instance ports, all, or module names directly.\n"
                "- State names across registers, counters, fsms, buffers, and memories must be globally unique; "
                "prefix repeated per-instance state names such as out0_valid_reg and out1_valid_reg.\n"
                "- Every state.fsms[] entry must declare owner or use <instance>.<fsm> naming.\n"
                "- FSM owner must be top or an instances[].name.\n"
                "- FSMs must declare non-empty states, initial, and reset_state, and transitions must use those states.\n\n"
                f"{task_guidance}\n"
                "Previous invalid System-HIS JSON:\n"
                f"{previous_content.strip()}"
            ),
        },
    ]


def _system_his_v12_task_guidance(task_type: str) -> str:
    if task_type == "alu_control_unit":
        return (
            "Required architecture for alu_control_unit:\n"
            "- components: control_decode, alu_core, status_flags\n"
            "- instances: decoder, core, flags\n"
            "- top ports must include clk, rst_n, valid, ready, op, lhs, rhs, result_valid, "
            "result, zero, carry, and negative.\n"
            "- op must be a 3-bit input; lhs, rhs, and result must match the requested width.\n"
            "- status_flags owns result, result_valid, zero, carry, and negative state if outputs are registered.\n"
            "- data_flow must describe opcode decode, ALU execution, and registered status output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/control_decode.v, rtl/alu_core.v, "
            "and rtl/status_flags.v."
        )
    if task_type == "crc_stream_checker":
        return (
            "Required architecture for crc_stream_checker:\n"
            "- components: stream_frame_accumulator, crc8_update, crc_status\n"
            "- instances: accumulator, update, status\n"
            "- top ports must include clk, rst_n, in_valid, in_data, frame_start, frame_end, "
            "expected_crc, out_ready, in_ready, out_valid, crc_value, and crc_match.\n"
            "- in_data must match the requested width; expected_crc and crc_value must be 8-bit ports.\n"
            "- stream_frame_accumulator owns crc_state, frame_crc, and frame_done state; "
            "crc_status owns out_valid, crc_value, and crc_match state.\n"
            "- data_flow must describe valid-ready byte input, CRC-8 update, frame completion, and match status output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/stream_frame_accumulator.v, "
            "rtl/crc8_update.v, and rtl/crc_status.v."
        )
    if task_type == "composed_dual_stream_join":
        return (
            "Required architecture for composed_dual_stream_join:\n"
            "- components: skid_buffer, stream_join, accumulator_core, stream_stage\n"
            "- instances: in0_buffer, in1_buffer, join_core, accumulator, out_stage\n"
            "- top ports must include clk, rst_n, in0_valid, in0_data, in1_valid, in1_data, out_ready, "
            "in0_ready, in1_ready, out_valid, and out_data.\n"
            "- Do not collapse this topology into one fused component.\n"
            "- Do not use Verilog reserved keywords such as fork, join, or buf as instance names.\n"
            "- in0_buffer and in1_buffer must both reference component skid_buffer.\n"
            "- data_flow must use named path arrays, not from/to-only edges.\n"
            "- data_flow.timing entries must use concrete integer latency_cycles and initiation_interval values.\n"
            "- valid and ready data_flow paths must explicitly connect join_core.out_valid, accumulator.sample_valid, "
            "out_stage.in_valid, out_stage.in_ready, accumulator.sample_ready, and join_core.out_ready.\n"
            "- accumulator_core.sample_valid must remain a single input port and accumulator_core.sample_ready "
            "must remain a single input port in this topology.\n"
            "- Do not introduce accumulator_core sample_valid_in, sample_valid_out, sample_ready_in, or "
            "sample_ready_out aliases.\n"
            "- control_flow entries must each include name, kind, when/effect for structured rules, related_state, and related_flows.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/skid_buffer.v, rtl/stream_join.v, "
            "rtl/accumulator_core.v, and rtl/stream_stage.v."
        )
    if task_type == "composed_vector_mac_pipeline":
        return (
            "Required architecture for composed_vector_mac_pipeline:\n"
            "- components: skid_buffer, vector_mac_core, stream_stage\n"
            "- instances: feature_buffer, weight_buffer, mac_core, score_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- feature_buffer and weight_buffer must both reference component skid_buffer.\n"
            "- vector_mac_core owns vector_index, accumulator, and pending_score state.\n"
            "- If a mac_core_fsm is used, declare it with owner mac_core, states IDLE/ACCUMULATE/OUTPUT, "
            "initial IDLE, reset_state IDLE, and transitions that reference those exact states.\n"
            "- top ports must include feature_valid, feature_data, feature_ready, weight_valid, "
            "weight_data, weight_ready, bias, score_valid, score_data, and score_ready.\n"
            "- data_flow must pair feature and weight streams into vector_mac_core and stage score output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/skid_buffer.v, "
            "rtl/vector_mac_core.v, and rtl/stream_stage.v."
        )
    if task_type == "composed_td_update_core":
        return (
            "Required architecture for composed_td_update_core:\n"
            "- components: td_input_stage, discount_core, td_update_core, stream_stage\n"
            "- instances: input_stage, discount, update, output_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include in_valid, in_ready, reward, value, next_value, gamma, alpha, "
            "out_valid, out_ready, td_error, and updated_value.\n"
            "- td_input_stage owns captured reward/value/next_value state.\n"
            "- td_update_core or stream_stage owns td_error and updated_value state if registered.\n"
            "- If an output_stage FSM is used, declare it with owner output_stage, states IDLE/VALID, "
            "initial IDLE, reset_state IDLE, and transitions that reference those exact states.\n"
            "- data_flow must describe tuple capture, discount calculation, TD update, and output staging.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/td_input_stage.v, rtl/discount_core.v, "
            "rtl/td_update_core.v, and rtl/stream_stage.v."
        )
    if task_type == "composed_policy_value_shell":
        return (
            "Required architecture for composed_policy_value_shell:\n"
            "- components: config_reg_bank, observation_stage, policy_score_core, action_select_core, stream_stage\n"
            "- instances: config, observation, score, select, output_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include cfg_valid, cfg_ready, cfg_addr, cfg_data, obs_valid, obs_ready, "
            "obs0, obs1, action_valid, action_ready, selected_action, and value_estimate.\n"
            "- config_reg_bank owns weight0, weight1, bias0, bias1, and enable state.\n"
            "- observation_stage owns captured observation state; stream_stage owns registered output state.\n"
            "- data_flow must describe config writes, observation capture, policy scoring, action selection, "
            "and output staging.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/config_reg_bank.v, rtl/observation_stage.v, "
            "rtl/policy_score_core.v, rtl/action_select_core.v, and rtl/stream_stage.v."
        )
    if task_type == "composed_replay_sample_shell":
        return (
            "Required architecture for composed_replay_sample_shell:\n"
            "- components: host_sample_stage, replay_store, sample_pack_core, sample_read_stage, occupancy_counter\n"
            "- instances: host_stage, store, pack, read_stage, occupancy\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include host_valid, host_ready, host_state, host_action, host_reward, "
            "host_next_state, host_done, sample_valid, sample_ready, sample_state, sample_action, "
            "sample_reward, sample_next_state, sample_done, and occupancy.\n"
            "- replay_store owns replay_entries, write_ptr, read_ptr, and occupancy state.\n"
            "- host_sample_stage owns staged host sample state; sample_read_stage owns staged output sample state.\n"
            "- data_flow must describe host sample staging, replay store write/read, sample packing, "
            "fabric-side output staging, and occupancy reporting.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/host_sample_stage.v, rtl/replay_store.v, "
            "rtl/sample_pack_core.v, rtl/sample_read_stage.v, and rtl/occupancy_counter.v."
        )
    if task_type == "composed_host_protocol_shell":
        return (
            "Required architecture for composed_host_protocol_shell:\n"
            "- components: axi_lite_write_ctrl, axi_lite_read_ctrl, control_reg_bank, sample_stream_adapter, irq_status\n"
            "- instances: write_ctrl, read_ctrl, regs, stream, irq\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include s_axi_awvalid, s_axi_awready, s_axi_awaddr, s_axi_wvalid, "
            "s_axi_wready, s_axi_wdata, s_axi_wstrb, s_axi_bvalid, s_axi_bready, "
            "s_axi_arvalid, s_axi_arready, s_axi_araddr, s_axi_rvalid, s_axi_rready, "
            "s_axi_rdata, m_axis_tvalid, m_axis_tready, m_axis_tdata, m_axis_tlast, and irq.\n"
            "- control_reg_bank owns ctrl, sample0, sample1, busy, done, and irq_state.\n"
            "- data_flow must describe write capture, readback, stream output, stream_done feedback, and irq output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/axi_lite_write_ctrl.v, rtl/axi_lite_read_ctrl.v, "
            "rtl/control_reg_bank.v, rtl/sample_stream_adapter.v, and rtl/irq_status.v."
        )
    if task_type == "composed_rl_accelerator_shell":
        return (
            "Required architecture for composed_rl_accelerator_shell:\n"
            "- components: host_config_bank, sample_capture_stage, policy_value_core, td_update_core, result_stream_stage\n"
            "- instances: config, sample, policy, update, result\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include cfg_valid, cfg_ready, cfg_addr, cfg_data, sample_valid, sample_ready, "
            "obs0, obs1, reward, next_value, done_in, result_valid, result_ready, selected_action, "
            "value_estimate, updated_value, episode_done, and irq.\n"
            "- host_config_bank owns weight0, bias0, weight1, bias1, alpha, and enable state.\n"
            "- sample_capture_stage owns captured sample tuple state; result_stream_stage owns result and irq state.\n"
            "- data_flow must describe config writes, sample capture, policy/value scoring, TD update, result staging, "
            "and irq output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/host_config_bank.v, rtl/sample_capture_stage.v, "
            "rtl/policy_value_core.v, rtl/td_update_core.v, and rtl/result_stream_stage.v."
        )
    if task_type == "composed_batch_rl_accelerator_shell":
        return (
            "Required architecture for composed_batch_rl_accelerator_shell:\n"
            "- components: batch_config_bank, batch_sample_buffer, dual_policy_value_core, "
            "dual_td_update_core, batch_result_stage\n"
            "- instances: config, batch, policy, update, result\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include cfg_valid, cfg_ready, cfg_addr, cfg_data, batch_valid, batch_ready, "
            "obs0_a, obs1_a, reward_a, next_value_a, done_a, obs0_b, obs1_b, reward_b, next_value_b, "
            "done_b, result_valid, result_ready, selected_action_a, value_estimate_a, updated_value_a, "
            "selected_action_b, value_estimate_b, updated_value_b, batch_done, and irq.\n"
            "- batch_config_bank owns shared weight0, bias0, weight1, bias1, alpha, and enable state.\n"
            "- batch_sample_buffer owns captured lane sample state; batch_result_stage owns lane result and irq state.\n"
            "- data_flow must describe config writes, two-lane batch capture, dual-lane policy/value scoring, "
            "dual-lane TD update, result staging, and irq output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/batch_config_bank.v, rtl/batch_sample_buffer.v, "
            "rtl/dual_policy_value_core.v, rtl/dual_td_update_core.v, and rtl/batch_result_stage.v."
        )
    if task_type == "composed_replay_arbiter_shell":
        return (
            "Required architecture for composed_replay_arbiter_shell:\n"
            "- components: host_transition_packetizer, replay_index_allocator, replay_request_arbiter, "
            "replay_memory_bank, sample_packet_stage\n"
            "- instances: packetizer, allocator, arbiter, memory, sample_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include host_valid, host_ready, host_state, host_action, host_reward, "
            "host_next_state, host_done, sample_req_valid, sample_req_ready, sample_index, sample_valid, "
            "sample_ready, sample_state, sample_action, sample_reward, sample_next_state, sample_done, "
            "occupancy, write_index, and irq.\n"
            "- replay_index_allocator owns write_index and occupancy; replay_memory_bank owns replay_entries; "
            "sample_packet_stage owns staged sample outputs and irq.\n"
            "- data_flow must describe host transition packetization, replay write allocation, read arbitration, "
            "memory readback, sample packet staging, and irq output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/host_transition_packetizer.v, "
            "rtl/replay_index_allocator.v, rtl/replay_request_arbiter.v, rtl/replay_memory_bank.v, "
            "and rtl/sample_packet_stage.v."
        )
    if task_type == "composed_stream_fork":
        return (
            "Required architecture for composed_stream_fork:\n"
            "- components: skid_buffer, stream_fork, stream_stage\n"
            "- instances: input_buffer, fork_core, out0_stage, out1_stage\n"
            "- top ports must include clk, rst_n, in_valid, in_data, in_ready, out0_valid, out0_data, "
            "out0_ready, out1_valid, out1_data, and out1_ready.\n"
            "- Do not collapse this topology into one fused component.\n"
            "- Do not use Verilog reserved keywords such as fork, join, or buf as instance names.\n"
            "- data_flow must explicitly connect both output payload paths and the corresponding valid/ready paths.\n"
            "- data_flow must use named path arrays and control_flow must reference existing state and flows."
        )
    if task_type == "composed_stream_accumulator":
        return (
            "Required architecture for composed_stream_accumulator:\n"
            "- components: skid_buffer, accumulator_core\n"
            "- instances: input_buffer, accumulator\n"
            "- top ports must include clk, rst_n, in_valid, in_data, in_ready, sample_valid, and sum.\n"
            "- accumulator_core ports must be clk, rst_n, sample_valid, sample, sample_ready, and sum; "
            "sample_valid must be an input and sample_ready must be an output.\n"
            "- Do not introduce sample_valid_in, sample_valid_out, or extra accumulator_core valid aliases.\n"
            "- data_flow must explicitly connect top.in_valid to input_buffer.in_valid, "
            "input_buffer.out_valid to accumulator.sample_valid, and accumulator.sample_valid to top.sample_valid.\n"
            "- data_flow must use named path arrays and control_flow must reference existing state and flows."
        )
    if task_type == "composed_event_counter":
        return (
            "Required architecture for composed_event_counter:\n"
            "- components: event_gate, counter_core\n"
            "- instances: event_gate, counter\n"
            "- data_flow must use named path arrays and control_flow must reference existing state and flows."
        )
    return ""


def _system_his_v12_retry_guidance(task_type: str) -> str:
    common = (
        "Task-specific retry guidance after checker failure:\n"
        "- Do not leave fsm, from, to, effect.action, or effect.target empty.\n"
        "- Do not emit fsm_transition unless state.fsms declares that FSM and its states.\n"
        "- If no FSM is needed, use handshake_rule, enable_rule, or stall_rule instead.\n"
    )
    if task_type == "composed_dual_stream_join":
        return (
            common
            + "- Required top ports: clk, rst_n, in0_valid, in0_data, in1_valid, in1_data, out_ready, "
            "in0_ready, in1_ready, out_valid, out_data\n"
            "- data_flow.timing entries must use integer latency_cycles >= 0 and initiation_interval > 0.\n"
            "- Connect join_core.out_valid to accumulator.sample_valid and out_stage.in_valid through explicit data_flow paths.\n"
            "- Connect out_stage.in_ready to accumulator.sample_ready and join_core.out_ready through explicit ready paths.\n"
            "- accumulator_core.sample_valid must remain a single input port; accumulator_core.sample_ready "
            "must remain a single input port.\n"
            "- Do not create sample_valid_in, sample_valid_out, sample_ready_in, or sample_ready_out aliases.\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_stream_accumulator":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, in_data, in_ready, sample_valid, sum\n"
            "- Connect input_buffer.out_valid to accumulator.sample_valid and top.sample_valid through explicit data_flow paths.\n"
            "- Do not leave top.sample_valid declared but disconnected.\n"
            "- accumulator_core.sample_valid must be an input port; accumulator_core.sample_ready must be an output port.\n"
            "- Do not create sample_valid_in, sample_valid_out, or extra accumulator_core valid aliases.\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_stream_fork":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, in_data, in_ready, out0_valid, out0_data, "
            "out0_ready, out1_valid, out1_data, out1_ready\n"
            "- If an FSM is declared for the skid buffer, initial and reset_state must be one of the declared states.\n"
            "- Prefer handshake_rule and buffer_occupancy control rules when an explicit FSM is not necessary.\n"
        )
    if task_type == "alu_control_unit":
        return (
            common
            + "- Required top ports: clk, rst_n, valid, ready, op, lhs, rhs, result_valid, result, zero, carry, negative\n"
            "- Keep control_decode, alu_core, and status_flags as separate RTL modules.\n"
            "- Do not rename op/lhs/rhs/result or collapse flag outputs into a packed status bus.\n"
        )
    if task_type == "crc_stream_checker":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, in_data, frame_start, frame_end, expected_crc, out_ready, in_ready, out_valid, crc_value, crc_match\n"
            "- Keep stream_frame_accumulator, crc8_update, and crc_status as separate RTL modules.\n"
            "- Do not rename frame_start/frame_end/expected_crc to AXI-style sideband names.\n"
        )
    if task_type == "composed_vector_mac_pipeline":
        return (
            common
            + "- Required top ports: clk, rst_n, feature_valid, feature_data, weight_valid, "
            "weight_data, bias, score_ready, feature_ready, weight_ready, score_valid, score_data\n"
            "- If mac_core_fsm is declared, it must have owner mac_core, states IDLE/ACCUMULATE/OUTPUT, "
            "initial IDLE, reset_state IDLE, and all fsm_transition rules must use those exact from/to states.\n"
            "- control_flow.effect must be an object with a non-empty declared target; prefer counter_update or enable_rule "
            "when the rule updates vector_index, accumulator, or pending_score.\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_td_update_core":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, reward, value, next_value, gamma, alpha, "
            "out_ready, in_ready, out_valid, td_error, updated_value\n"
            "- If out_fsm is declared, use owner output_stage, states IDLE/VALID, initial IDLE, reset_state IDLE, "
            "and all fsm_transition rules must use fsm out_fsm with those exact from/to states.\n"
            "- control_flow.effect must be an object with a non-empty declared target; prefer handshake_rule "
            "when modeling output valid/ready behavior.\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_policy_value_shell":
        return (
            common
            + "- Required top ports: clk, rst_n, cfg_valid, cfg_addr, cfg_data, cfg_ready, obs_valid, "
            "obs_ready, obs0, obs1, action_valid, action_ready, selected_action, value_estimate\n"
            "- Keep config_reg_bank, observation_stage, policy_score_core, action_select_core, and stream_stage "
            "as separate RTL modules.\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_replay_sample_shell":
        return (
            common
            + "- Required top ports: clk, rst_n, host_valid, host_ready, host_state, host_action, "
            "host_reward, host_next_state, host_done, sample_valid, sample_ready, sample_state, "
            "sample_action, sample_reward, sample_next_state, sample_done, occupancy\n"
            "- Keep host_sample_stage, replay_store, sample_pack_core, sample_read_stage, and "
            "occupancy_counter as separate RTL modules.\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_host_protocol_shell":
        return (
            common
            + "- Required top ports: clk, rst_n, s_axi_awvalid, s_axi_awready, s_axi_awaddr, "
            "s_axi_wvalid, s_axi_wready, s_axi_wdata, s_axi_wstrb, s_axi_bvalid, s_axi_bready, "
            "s_axi_arvalid, s_axi_arready, s_axi_araddr, s_axi_rvalid, s_axi_rready, s_axi_rdata, "
            "m_axis_tvalid, m_axis_tready, m_axis_tdata, m_axis_tlast, irq\n"
            "- Keep axi_lite_write_ctrl, axi_lite_read_ctrl, control_reg_bank, sample_stream_adapter, "
            "and irq_status as separate RTL modules.\n"
            "- This task intentionally uses AXI-style signal names; preserve them exactly.\n"
        )
    if task_type == "composed_rl_accelerator_shell":
        return (
            common
            + "- Required top ports: clk, rst_n, cfg_valid, cfg_ready, cfg_addr, cfg_data, sample_valid, "
            "sample_ready, obs0, obs1, reward, next_value, done_in, result_valid, result_ready, "
            "selected_action, value_estimate, updated_value, episode_done, irq\n"
            "- Keep host_config_bank, sample_capture_stage, policy_value_core, td_update_core, and "
            "result_stream_stage as separate RTL modules.\n"
            "- This is a synthetic integrated RL accelerator shell; do not claim real DQN, PPO, SAC, DMA, "
            "or board-level semantics without reference inputs.\n"
        )
    if task_type == "composed_batch_rl_accelerator_shell":
        return (
            common
            + "- Required top ports: clk, rst_n, cfg_valid, cfg_ready, cfg_addr, cfg_data, batch_valid, "
            "batch_ready, obs0_a, obs1_a, reward_a, next_value_a, done_a, obs0_b, obs1_b, reward_b, "
            "next_value_b, done_b, result_valid, result_ready, selected_action_a, value_estimate_a, "
            "updated_value_a, selected_action_b, value_estimate_b, updated_value_b, batch_done, irq\n"
            "- Keep batch_config_bank, batch_sample_buffer, dual_policy_value_core, dual_td_update_core, "
            "and batch_result_stage as separate RTL modules.\n"
            "- This is a synthetic two-lane batch RL accelerator shell; do not claim real DQN, PPO, SAC, DMA, "
            "or board-level semantics without reference inputs.\n"
        )
    if task_type == "composed_replay_arbiter_shell":
        return (
            common
            + "- Required top ports: clk, rst_n, host_valid, host_ready, host_state, host_action, "
            "host_reward, host_next_state, host_done, sample_req_valid, sample_req_ready, sample_index, "
            "sample_valid, sample_ready, sample_state, sample_action, sample_reward, sample_next_state, "
            "sample_done, occupancy, write_index, irq\n"
            "- Keep host_transition_packetizer, replay_index_allocator, replay_request_arbiter, "
            "replay_memory_bank, and sample_packet_stage as separate RTL modules.\n"
            "- This is a synthetic replay arbiter shell; do not claim random replay, prioritized replay, DMA, "
            "DDR, or board-level semantics without reference inputs.\n"
        )
    if task_type == "composed_stream_fork":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, in_data, out0_ready, out1_ready, "
            "in_ready, out0_valid, out0_data, out1_valid, out1_data\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_stream_accumulator":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, in_data, in_ready, sample_valid, sum\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_event_counter":
        return common + "- Required top ports: clk, rst_n, event_valid, count\n"
    return common


def _his_project_messages(
    request: ProjectRequest,
    platform: PlatformProfile,
    system_his: dict[str, Any],
) -> list[dict[str, str]]:
    system_his_text = json.dumps(system_his, ensure_ascii=False, indent=2)
    skeleton_files = build_contract_skeleton_project(request, platform, system_his).files
    skeleton_text = json.dumps(skeleton_files, ensure_ascii=False, indent=2)
    behavior_paths = [path for path, content in sorted(skeleton_files.items()) if "BEHAVIOR_HOLE" in content]
    behavior_entries = "\n".join(f'    "{path}": "...",' for path in behavior_paths).rstrip(",")
    system = (
        "You generate behavioral RTL bodies for checked System-HIS architecture contracts. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Generate behavior bodies for a contract-preserving SR2FPGA Verilog RTL skeleton.

Project:
- project_name: {request.project_name}
- task_type: {request.task_type}
- width: {request.width}
- user_prompt: {request.description or "No extra user prompt provided."}

Platform:
- name: {platform.name}
- vendor: {platform.vendor}
- toolchain: {platform.toolchain}
- clock_hz: {platform.clock_hz}
- reset_polarity: {platform.reset_polarity}

Checked System-HIS v1.2:
{system_his_text}

Contract-preserving deterministic skeleton:
{skeleton_text}

Rules:
- Treat the System-HIS as the frozen architecture contract.
- Use the deterministic skeleton as the structural source of truth.
- Preserve module headers, top-level port lists, instance names, parameter
  overrides, manifest sources, timing constraints, and testbench top instantiation
  from the skeleton.
- Fill BEHAVIOR_HOLE regions with behavioral RTL only; do not create structural
  names that are absent from the checked System-HIS.
- Do not change component, instance, top port, data_flow, or control_flow names.
- Generate RTL that implements the top-down architecture contract.
- Generated behavior must be Verilator -Wall clean: drive every declared output,
  include a default branch for every case statement, avoid incomplete case
  coverage, and do not create multiple continuous drivers for the same signal.
- Make arithmetic widths explicit. For fixed-point multiply/add/shift paths,
  assign DATA_WIDTH outputs from an explicitly sized intermediate or slice such
  as value_ext[DATA_WIDTH-1:0]; do not rely on implicit Verilog truncation or
  extension that would trigger WIDTHEXPAND or WIDTHTRUNC.
- If a wide intermediate is sliced, either use every bit or add a local
  _unused_* reduction wire for intentionally unused high/low bits so Verilator
  does not report UNUSEDSIGNAL on partial product bits.
- Use declared FSM state localparams from the deterministic skeleton when
  implementing state machines.
- Do not rename, omit, or replace System-HIS state.fsms states; every declared
  state name must remain visible in the generated RTL module.
- Do not use Verilog reserved keywords for any RTL identifier, including modules,
  instances, regs, wires, arrays, blocks, and parameters. Avoid names such as
  fork, join, buf, begin, end, module, wire, input, output, and reg.
- Do not return system_his.json, manifest.json, rtl/top.v, constraints, testbench,
  reports, complete modules, module headers, or endmodule lines.
- The deterministic skeleton already supplies structure, constraints, manifest,
  reports, and testbench. Your output supplies only replacement text for each
  BEHAVIOR_HOLE marker.
{_icarus_testbench_rules()}

Behavior files with BEHAVIOR_HOLE markers:
{json.dumps(behavior_paths, ensure_ascii=False, indent=2)}

Return JSON in this exact shape. The value of each behavior file must be a JSON
string; escape newlines as \\n and escape any double quotes inside file contents:
{{
  "behavior_files": {{
{behavior_entries}
  }}
}}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _with_his_project_retry_feedback(
    messages: list[dict[str, str]],
    error: str,
    previous_content: str,
) -> list[dict[str, str]]:
    return [
        *messages,
        {"role": "assistant", "content": previous_content or "{}"},
        {
            "role": "user",
            "content": (
                "Your previous behavior_files output failed validation. "
                "Repair that JSON in place and return a corrected complete behavior_files JSON object only.\n\n"
                "Validation error:\n"
                f"{error}\n\n"
                "HIS2PROJECT behavior repair checklist:\n"
                "- Return behavior_files only, not files.\n"
                "- Each behavior_files value must contain only the replacement body for one BEHAVIOR_HOLE.\n"
                "- Do not include module declarations, module headers, port lists, or endmodule lines.\n"
                "- Do not return system_his.json, manifest.json, rtl/top.v, constraints, testbench, or reports.\n"
                "- Drive every declared output in the behavior body.\n"
                "- Every case statement must include a default branch or cover all encoded states.\n"
                "- Make arithmetic widths explicit; avoid implicit truncation/extension warnings such as WIDTHEXPAND or WIDTHTRUNC.\n"
                "- If a wide intermediate is sliced, consume intentionally unused high/low bits with a local _unused_* reduction wire.\n"
                "- Avoid undriven signals, incomplete case coverage, and multiple continuous drivers.\n\n"
                "Previous invalid behavior_files JSON:\n"
                f"{previous_content.strip()}"
            ),
        },
    ]


def _project_messages(request: ProjectRequest, platform: PlatformProfile) -> list[dict[str, str]]:
    required_files = "\n".join(f"- {path}" for path in sorted(REQUIRED_PROJECT_FILES))
    rtl_contract = _rtl_contract_for_task(request.task_type)
    system = (
        "You generate complete FPGA RTL project packages as JSON. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Generate a Verilog RTL project package for SR2FPGA.

Project:
- project_name: {request.project_name}
- task_type: {request.task_type}
- width: {request.width}
- description: {request.description or "No extra description provided."}

Platform:
- name: {platform.name}
- vendor: {platform.vendor}
- toolchain: {platform.toolchain}
- clock_hz: {platform.clock_hz}
- reset_polarity: {platform.reset_polarity}

Required files:
{required_files}

RTL structure:
{rtl_contract}

Return JSON in this exact shape. The value of each file must be a JSON string;
escape newlines as \\n and escape any double quotes inside file contents:
{{
  "files": {{
    "system_his.json": "...",
    "manifest.json": "...",
    "rtl/top.v": "...",
{_additional_project_file_entries(request.task_type)}
    "constraints/timing.sdc": "...",
    "sim/tb_top.v": "...",
    "reports/predicted_qor.json": "..."
  }}
}}

The manifest.json file content must itself be JSON and must contain this tool
pipeline schema:
{{
  "project_name": "{request.project_name}",
  "top_module": "top",
  "sources": {_manifest_sources_example(request.task_type)},
  "constraints": {{"timing": "constraints/timing.sdc"}},
  "simulation": {{"testbench": "sim/tb_top.v"}},
  "reports": ["reports/predicted_qor.json"]
}}

The Verilog must be synthesizable and the testbench must print TEST_PASS on success.
{_icarus_testbench_rules()}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _repair_messages(project: GeneratedProject, diagnosis: dict[str, object]) -> list[dict[str, str]]:
    files_text = "\n\n".join(
        f"### {path}\n{content}" for path, content in sorted(project.files.items())
    )
    diagnosis_text = json.dumps(diagnosis, ensure_ascii=False, indent=2)
    required_files = "\n".join(f"- {path}" for path in sorted(REQUIRED_PROJECT_FILES))
    task_type = _project_task_type(project.files)
    rtl_contract = _repair_rtl_contract(project.files, task_type)
    system_his_prompt = _repair_system_his_prompt(project.files, project.project_name)
    edit_surface_rules = _repair_edit_surface_rules(project, diagnosis)
    system = (
        "You repair FPGA RTL project packages as JSON. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Repair this SR2FPGA project package.

Failure diagnosis:
{diagnosis_text}

Current project files:
{files_text}

Required files:
{required_files}

RTL structure:
{rtl_contract}

Preserve every file that is not needed for the fix byte-for-byte. If
manifest.json already has a valid top_module, sources, and simulation.testbench,
copy the original manifest.json unchanged unless the failure log specifically
points to manifest.json.

Return JSON in this exact shape. The value of each file must be a JSON string;
escape newlines as \\n and escape any double quotes inside file contents:
{{
  "files": {{
    "system_his.json": "...",
    "manifest.json": "...",
    "rtl/top.v": "...",
{_additional_repair_file_entries(project.files, task_type)}
    "constraints/timing.sdc": "...",
    "sim/tb_top.v": "...",
    "reports/predicted_qor.json": "..."
  }}
}}

The manifest.json file content must itself be JSON and must contain this tool
pipeline schema:
{{
  "project_name": "{project.project_name}",
  "top_module": "top",
  "sources": {_repair_sources_example(project.files, task_type)},
  "constraints": {{"timing": "constraints/timing.sdc"}},
  "simulation": {{"testbench": "sim/tb_top.v"}},
  "reports": ["reports/predicted_qor.json"]
}}

{system_his_prompt}

{edit_surface_rules}

Make the smallest practical fix for the failing tool log. Preserve pure
Verilog RTL and ensure the testbench prints TEST_PASS on success.
Repair quality rules:
- Do not introduce a new syntax error while fixing a lint warning.
- Use legal Verilog concatenation syntax: nested replication must be wrapped
  as {{ {{N{{bit}}}}, signal }}; never write {{N{{bit}}, signal}}.
- After a lint repair, the edited RTL must still be Verilator -Wall clean:
  avoid WIDTHEXPAND, WIDTHTRUNC, UNUSEDSIGNAL, UNDRIVEN, and PINNOTFOUND.
{_icarus_testbench_rules()}
{_unused_parameter_repair_rules(diagnosis)}
{_functional_mismatch_repair_rules(diagnosis)}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _repair_edit_surface_rules(project: GeneratedProject, diagnosis: dict[str, object]) -> str:
    rules = [
        "Allowed edit surface:",
        "- Copy trusted artifacts byte-for-byte, including testbenches, golden models, hidden tests, "
        "scoreboards, protocol checkers, constraints, and board files.",
        "- Do not add, delete, or rename RTL source files.",
    ]
    has_behavior_regions = any(
        BEHAVIOR_REGION_BEGIN in content or BEHAVIOR_REGION_END in content
        for path, content in project.files.items()
        if path.startswith("rtl/")
    )
    if has_behavior_regions:
        rules.extend(
            [
                f"- Only edit text between {BEHAVIOR_REGION_BEGIN} and {BEHAVIOR_REGION_END} markers.",
                "- Preserve the markers and every byte outside each marked region.",
                "- Do not modify unmarked RTL files such as the deterministic top shell.",
            ]
        )
    elif str(diagnosis.get("stage", "")) == "l0_consistency":
        rules.append(
            "- An RTL interface change is allowed only to restore the declared System-HIS contract; "
            "keep all unrelated RTL structure unchanged."
        )
    else:
        rules.append("- Preserve module names, parameters, and ports; edit implementation logic only.")
    return "\n".join(rules)


def _icarus_testbench_rules() -> str:
    return (
        "Testbench portability rules:\n"
        "- The testbench must compile with Icarus Verilog using iverilog -g2012.\n"
        "- Do not initialize unpacked arrays with aggregate literals such as "
        "`reg [7:0] seq [0:2] = {8'd1, 8'd2, 8'd3};`.\n"
        "- Use initial block assignments instead, for example `seq[0] = 8'd1;`.\n"
        "- Drive and withdraw valid-ready stimulus away from the DUT sampling edge, "
        "for example on negedge clk for posedge-clocked RTL.\n"
        "- Do not hold input valid high until out_valid; deassert or advance each "
        "input valid after its own input ready handshake so one packet cannot be "
        "accepted repeatedly while the testbench waits for output.\n"
        "- Observe outputs after nonblocking assignments have settled, for example on "
        "negedge clk or after an explicit small delay from posedge clk.\n"
        "- After wait(out_valid), check the current transaction before advancing to another "
        "active clock edge; use a small delay or negedge observation in the same valid cycle.\n"
        "- Exercise back-to-back valid-ready transfers so stream buffers, joins, and "
        "accumulators cannot drop a sample between consecutive handshakes.\n"
        "- For streaming designs, check each output transaction against the expected "
        "sequence; do not only check the final output value.\n"
        "- Do not print TEST_PASS unconditionally. The testbench must print "
        "TEST_PASS only after conditional TEST_FAIL checks compare top-level "
        "observable outputs and status signals against expected behavior.\n"
        "- Every wait loop must be bounded with a cycle counter and must print TEST_FAIL on timeout."
    )


def _functional_mismatch_repair_rules(diagnosis: dict[str, object]) -> str:
    if str(diagnosis.get("failure_type", "")) != "functional_mismatch":
        return ""
    return (
        "Functional mismatch repair rules:\n"
        "- Do not make the testbench pass by changing expected values to match the observed wrong output.\n"
        "- For functional mismatches, prefer fixing RTL behavior, handshake timing, state updates, or reset behavior.\n"
        "- For valid-ready stream mismatches, check for each lost or duplicated valid-ready transfer before changing tests.\n"
        "- Only change expected values when the diagnosis explicitly says the testbench expectation is wrong."
    )


def _unused_parameter_repair_rules(diagnosis: dict[str, object]) -> str:
    if "unusedparam" not in str(diagnosis.get("root_cause", "")).lower():
        return ""
    return (
        "Unused parameter repair rules:\n"
        "- If you remove an unused parameter, the module declaration and every instantiation must agree.\n"
        "- Either use the parameter in real RTL logic, or remove the parameter override from all instantiations.\n"
        "- Do not silence a lint warning by creating a new PINNOTFOUND or parameter mismatch error."
    )


def _rtl_contract_for_task(task_type: str) -> str:
    example_sources = MULTIMODULE_RTL_EXAMPLES.get(task_type)
    if example_sources is None:
        return (
            "Single-file RTL is allowed for this task. Put the synthesizable top module in "
            "rtl/top.v and list it in manifest.json sources."
        )
    return (
        "Generate a true multi-file RTL implementation. rtl/top.v must be an integration wrapper "
        "that instantiates task-specific submodules. Generate at least two additional Verilog "
        f"source files for this task. Recommended source list: {json.dumps(example_sources)}. "
        "List every RTL source in manifest.json sources and include every listed source in files."
    )


def _manifest_sources_example(task_type: str) -> str:
    return json.dumps(MULTIMODULE_RTL_EXAMPLES.get(task_type, ["rtl/top.v"]))


def _artifact_sources_example(system_his: dict[str, Any], task_type: str) -> list[str]:
    artifacts = system_his.get("artifacts")
    if isinstance(artifacts, dict):
        sources = artifacts.get("rtl_sources")
        if isinstance(sources, list) and all(isinstance(source, str) for source in sources):
            if "rtl/top.v" in sources:
                return sources
    return MULTIMODULE_RTL_EXAMPLES.get(task_type, ["rtl/top.v"])


def _additional_project_file_entries(task_type: str) -> str:
    return _additional_file_entries(MULTIMODULE_RTL_EXAMPLES.get(task_type, ["rtl/top.v"]))


def _additional_file_entries(sources: list[str]) -> str:
    extra_sources = [source for source in sources if source != "rtl/top.v"]
    if not extra_sources:
        return ""
    return "".join(f'    "{source}": "...",\n' for source in extra_sources)


def _repair_rtl_contract(files: dict[str, str], task_type: str | None) -> str:
    if task_type in MULTIMODULE_RTL_EXAMPLES:
        return (
            "Preserve the true multi-file RTL structure. Do not collapse submodules into rtl/top.v. "
            "rtl/top.v must remain an integration wrapper, and manifest.json sources must keep "
            "rtl/top.v plus at least two submodule .v files unless the failure specifically requires "
            "renaming a source."
        )
    try:
        manifest = json.loads(files.get("manifest.json", "{}"))
    except json.JSONDecodeError:
        manifest = {}
    sources = manifest.get("sources")
    rtl_sources = sources if isinstance(sources, list) else []
    if len([path for path in rtl_sources if isinstance(path, str) and path.endswith(".v")]) >= 3:
        return (
            "Preserve the existing multi-file RTL structure. Do not collapse submodules into rtl/top.v. "
            "Return all existing source files unless the repair requires adding or renaming one."
        )
    return "Preserve the existing RTL source structure unless the failure requires changing it."


def _repair_sources_example(files: dict[str, str], task_type: str | None) -> str:
    try:
        manifest = json.loads(files.get("manifest.json", "{}"))
    except json.JSONDecodeError:
        manifest = {}
    sources = manifest.get("sources")
    if isinstance(sources, list) and all(isinstance(path, str) for path in sources):
        return json.dumps(sources)
    if task_type in MULTIMODULE_RTL_EXAMPLES:
        return json.dumps(MULTIMODULE_RTL_EXAMPLES[task_type])
    return json.dumps(["rtl/top.v"])


def _additional_repair_file_entries(files: dict[str, str], task_type: str | None) -> str:
    try:
        sources = json.loads(_repair_sources_example(files, task_type))
    except json.JSONDecodeError:
        sources = ["rtl/top.v"]
    if not isinstance(sources, list) or not all(isinstance(source, str) for source in sources):
        sources = ["rtl/top.v"]
    return _additional_file_entries(sources)


def _repair_system_his_prompt(files: dict[str, str], project_name: str) -> str:
    if _project_system_his_schema(files) == SYSTEM_HIS_V12_SCHEMA:
        return (
            "The system_his.json file content must itself be JSON. Preserve the existing "
            "canonical System-HIS v1.2 contract unless the diagnosis explicitly names system_his.json. "
            "Keep schema_version system-his-v1.2 and do not change top, state, components, instances, "
            "data_flow, control_flow, or artifacts.\n"
            "Current canonical System-HIS v1.2 contract:\n"
            f"{files.get('system_his.json', '{}').strip()}"
        )
    return (
        "The system_his.json file content must itself be JSON and must follow this\n"
        "system-his-v1.1 structure-contract schema:\n"
        f"{_system_his_contract(project_name)}"
    )


def _system_his_contract(project_name: str) -> str:
    return (
        json.dumps(
            {
            "schema_version": "system-his-v1.1",
            "project_name": project_name,
            "project": {"name": project_name, "description": "short requirement summary", "top": "top"},
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [{"name": "rst_n", "polarity": "active_low", "kind": "sync"}],
            "system": {"description": "short black-box behavior summary"},
            "interface": {"top_module": "top", "ports": []},
            "architecture": {"top_module": "top", "topology": {"nodes": [], "edges": []}},
            "modules": [
                {
                    "name": "top",
                    "role": "top",
                    "source": "rtl/top.v",
                    "ports": [],
                    "parameters": {},
                    "params": [],
                    "clock": "clk",
                    "reset": "rst_n",
                    "intent": "integrates submodules and exposes the top interface",
                },
                {
                    "name": "submodule_name",
                    "role": "submodule",
                    "source": "rtl/submodule_name.v",
                    "ports": [],
                    "parameters": {"WIDTH": 8},
                    "params": [{"name": "WIDTH", "value": 8}],
                    "clock": "clk",
                    "reset": "rst_n",
                    "intent": "one-line module intent",
                },
            ],
            "connections": [
                {
                    "from": {"module": "top", "port": "input_or_signal"},
                    "to": {"module": "submodule_name", "port": "input_or_signal"},
                    "signal": "signal_name",
                    "protocol": "register",
                    "width": 1,
                    "cdc": False,
                }
            ],
            "top_ports": [],
            "platform": {"toolchain": "open_source"},
            "verification": {
                "testbench": "sim/tb_top.v",
                "checks": ["l0_contract", "l1_lint", "l2_self_checking_sim", "l3_synthesis"],
                "test_pass_means": "testbench prints TEST_PASS and no TEST_FAIL",
            },
            "qor_intent": {"resources": {"lut": 0, "ff": 0, "bram": 0, "dsp": 0}},
            },
            indent=2,
        )
        + "\n\n"
        + "Important System-HIS rules: role must be exactly top or submodule; use clock, not clock_domain; "
        + "parameters must be an object of RTL-declared parameter names to values; params must be a list "
        + "of {name, value} entries matching parameters exactly; omit undeclared RTL parameters; port widths "
        + "must match the parsed RTL exactly, including expressions like [WIDTH-1:0]; width strings must "
        + "match parsed RTL ranges exactly rather than simplified parameter names; connection protocol "
        + "must be one of register, valid_ready, axi_lite, axi_stream; every connection needs from/to "
        + "endpoint objects, signal, width, and boolean cdc; connection endpoint module values must use "
        + "System-HIS module names, not instance aliases such as sb0, join, acc, or stg; Do not use "
        + "Verilog reserved keywords as any RTL identifier, including instance, signal, register, array, "
        + "block, and parameter names; avoid fork, join, buf, begin, end, module, wire, input, output, and reg."
    )
