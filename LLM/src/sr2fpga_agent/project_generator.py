"""Deterministic V1 project generator for small RTL tasks."""

from __future__ import annotations

import json
import re
from textwrap import dedent

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


SUPPORTED_TASK_TYPES = {
    "counter",
    "fifo",
    "simple_fsm",
    "ram_read_write",
    "uart_tx",
    "spi_master",
    "pwm_controller",
    "fir_filter",
    "streaming_valid_ready",
    "matrix_vector_mac",
    "composed_event_counter",
    "composed_stream_accumulator",
    "composed_stream_fork",
    "composed_dual_stream_join",
    "composed_vector_mac_pipeline",
    "composed_td_update_core",
    "composed_policy_value_shell",
    "composed_replay_sample_shell",
    "composed_host_protocol_shell",
    "composed_rl_accelerator_shell",
    "composed_batch_rl_accelerator_shell",
    "composed_replay_arbiter_shell",
}

COMPONENT_LIBRARY_ID = "sr2fpga_deterministic_components_v1"

COMPONENT_TOPOLOGIES = {
    "composed_event_counter": {
        "topology_id": "t1_event_counter",
        "difficulty_tier": "T1",
        "submodules": ["event_gate", "counter_core"],
        "nodes": [
            {"id": "gate", "component": "event_gate"},
            {"id": "counter", "component": "counter_core"},
        ],
        "edges": [
            {"from": "top.event_valid", "to": "event_gate.event_valid"},
            {"from": "event_gate.count_en", "to": "counter_core.en"},
            {"from": "counter_core.count", "to": "top.count"},
        ],
    },
    "composed_stream_accumulator": {
        "topology_id": "t2_stream_accumulator",
        "difficulty_tier": "T2",
        "submodules": ["skid_buffer", "accumulator_core"],
        "nodes": [
            {"id": "skid", "component": "skid_buffer"},
            {"id": "accum", "component": "accumulator_core"},
        ],
        "edges": [
            {"from": "top.in_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.in_data", "to": "skid_buffer.in_data"},
            {"from": "skid_buffer.out_valid", "to": "accumulator_core.sample_valid"},
            {"from": "skid_buffer.out_data", "to": "accumulator_core.sample"},
            {"from": "accumulator_core.sample_ready", "to": "skid_buffer.out_ready"},
            {"from": "accumulator_core.sum", "to": "top.sum"},
        ],
    },
    "composed_stream_fork": {
        "topology_id": "t3_stream_fork",
        "difficulty_tier": "T3",
        "submodules": ["skid_buffer", "stream_fork", "stream_stage"],
        "nodes": [
            {"id": "skid", "component": "skid_buffer"},
            {"id": "fork", "component": "stream_fork"},
            {"id": "stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.in_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.in_data", "to": "skid_buffer.in_data"},
            {"from": "skid_buffer.out_valid", "to": "stream_fork.in_valid"},
            {"from": "skid_buffer.out_data", "to": "stream_fork.in_data"},
            {"from": "stream_fork.in_ready", "to": "skid_buffer.out_ready"},
            {"from": "stream_fork.out0_valid", "to": "stream_stage.in_valid"},
            {"from": "stream_fork.out0_data", "to": "stream_stage.in_data"},
            {"from": "stream_stage.in_ready", "to": "stream_fork.out0_ready"},
            {"from": "stream_fork.out1_valid", "to": "stream_stage.in_valid"},
            {"from": "stream_fork.out1_data", "to": "stream_stage.in_data"},
            {"from": "stream_stage.in_ready", "to": "stream_fork.out1_ready"},
            {"from": "stream_stage.out_valid", "to": "top.out0_valid"},
            {"from": "stream_stage.out_data", "to": "top.out0_data"},
            {"from": "stream_stage.out_valid", "to": "top.out1_valid"},
            {"from": "stream_stage.out_data", "to": "top.out1_data"},
        ],
    },
    "composed_dual_stream_join": {
        "topology_id": "t4_dual_stream_join",
        "difficulty_tier": "T4",
        "submodules": ["skid_buffer", "stream_join", "accumulator_core", "stream_stage"],
        "nodes": [
            {"id": "skid_a", "component": "skid_buffer"},
            {"id": "skid_b", "component": "skid_buffer"},
            {"id": "join", "component": "stream_join"},
            {"id": "accum", "component": "accumulator_core"},
            {"id": "stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.in0_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.in0_data", "to": "skid_buffer.in_data"},
            {"from": "top.in1_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.in1_data", "to": "skid_buffer.in_data"},
            {"from": "skid_buffer.out_valid", "to": "stream_join.in0_valid"},
            {"from": "skid_buffer.out_data", "to": "stream_join.in0_data"},
            {"from": "skid_buffer.out_valid", "to": "stream_join.in1_valid"},
            {"from": "skid_buffer.out_data", "to": "stream_join.in1_data"},
            {"from": "stream_join.in0_ready", "to": "skid_buffer.out_ready"},
            {"from": "stream_join.in1_ready", "to": "skid_buffer.out_ready"},
            {"from": "stream_join.out_valid", "to": "accumulator_core.sample_valid"},
            {"from": "stream_join.out_data", "to": "accumulator_core.sample"},
            {"from": "accumulator_core.sample_ready", "to": "stream_join.out_ready"},
            {"from": "accumulator_core.sample_valid", "to": "stream_stage.in_valid"},
            {"from": "accumulator_core.sum", "to": "stream_stage.in_data"},
            {"from": "stream_stage.in_ready", "to": "accumulator_core.sample_ready"},
            {"from": "stream_stage.out_valid", "to": "top.out_valid"},
            {"from": "stream_stage.out_data", "to": "top.out_data"},
        ],
    },
    "composed_vector_mac_pipeline": {
        "topology_id": "t5_vector_mac_pipeline",
        "difficulty_tier": "T5",
        "submodules": ["skid_buffer", "vector_mac_core", "stream_stage"],
        "nodes": [
            {"id": "feature_buffer", "component": "skid_buffer"},
            {"id": "weight_buffer", "component": "skid_buffer"},
            {"id": "mac", "component": "vector_mac_core"},
            {"id": "score_stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.feature_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.feature_data", "to": "skid_buffer.in_data"},
            {"from": "top.weight_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.weight_data", "to": "skid_buffer.in_data"},
            {"from": "skid_buffer.out_valid", "to": "vector_mac_core.feature_valid"},
            {"from": "skid_buffer.out_data", "to": "vector_mac_core.feature_data"},
            {"from": "skid_buffer.out_valid", "to": "vector_mac_core.weight_valid"},
            {"from": "skid_buffer.out_data", "to": "vector_mac_core.weight_data"},
            {"from": "vector_mac_core.feature_ready", "to": "skid_buffer.out_ready"},
            {"from": "vector_mac_core.weight_ready", "to": "skid_buffer.out_ready"},
            {"from": "top.bias", "to": "vector_mac_core.bias"},
            {"from": "vector_mac_core.score_valid", "to": "stream_stage.in_valid"},
            {"from": "vector_mac_core.score_data", "to": "stream_stage.in_data"},
            {"from": "stream_stage.in_ready", "to": "vector_mac_core.score_ready"},
            {"from": "stream_stage.out_valid", "to": "top.score_valid"},
            {"from": "stream_stage.out_data", "to": "top.score_data"},
            {"from": "top.score_ready", "to": "stream_stage.out_ready"},
        ],
    },
    "composed_td_update_core": {
        "topology_id": "t6_td_update_core",
        "difficulty_tier": "T6",
        "submodules": ["td_input_stage", "discount_core", "td_update_core", "stream_stage"],
        "nodes": [
            {"id": "input_stage", "component": "td_input_stage"},
            {"id": "discount", "component": "discount_core"},
            {"id": "update", "component": "td_update_core"},
            {"id": "output_stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.in_valid", "to": "td_input_stage.in_valid"},
            {"from": "top.reward", "to": "td_input_stage.reward"},
            {"from": "top.value", "to": "td_input_stage.value"},
            {"from": "top.next_value", "to": "td_input_stage.next_value"},
            {"from": "top.gamma", "to": "td_input_stage.gamma"},
            {"from": "top.alpha", "to": "td_input_stage.alpha"},
            {"from": "td_input_stage.out_valid", "to": "discount_core.in_valid"},
            {"from": "td_input_stage.reward_out", "to": "discount_core.reward"},
            {"from": "td_input_stage.next_value_out", "to": "discount_core.next_value"},
            {"from": "td_input_stage.gamma_out", "to": "discount_core.gamma"},
            {"from": "discount_core.out_valid", "to": "td_update_core.in_valid"},
            {"from": "discount_core.discounted_return", "to": "td_update_core.discounted_return"},
            {"from": "td_input_stage.value_out", "to": "td_update_core.value"},
            {"from": "td_input_stage.alpha_out", "to": "td_update_core.alpha"},
            {"from": "td_update_core.out_valid", "to": "stream_stage.in_valid"},
            {"from": "td_update_core.td_error", "to": "stream_stage.td_error"},
            {"from": "td_update_core.updated_value", "to": "stream_stage.updated_value"},
            {"from": "stream_stage.out_valid", "to": "top.out_valid"},
            {"from": "stream_stage.td_error_out", "to": "top.td_error"},
            {"from": "stream_stage.updated_value_out", "to": "top.updated_value"},
            {"from": "top.out_ready", "to": "stream_stage.out_ready"},
        ],
    },
    "composed_policy_value_shell": {
        "topology_id": "t7_policy_value_shell",
        "difficulty_tier": "T7",
        "submodules": [
            "config_reg_bank",
            "observation_stage",
            "policy_score_core",
            "action_select_core",
            "stream_stage",
        ],
        "nodes": [
            {"id": "config", "component": "config_reg_bank"},
            {"id": "observation", "component": "observation_stage"},
            {"id": "score", "component": "policy_score_core"},
            {"id": "select", "component": "action_select_core"},
            {"id": "output_stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.cfg_valid", "to": "config_reg_bank.cfg_valid"},
            {"from": "top.cfg_addr", "to": "config_reg_bank.cfg_addr"},
            {"from": "top.cfg_data", "to": "config_reg_bank.cfg_data"},
            {"from": "config_reg_bank.cfg_ready", "to": "top.cfg_ready"},
            {"from": "top.obs_valid", "to": "observation_stage.in_valid"},
            {"from": "top.obs0", "to": "observation_stage.obs0"},
            {"from": "top.obs1", "to": "observation_stage.obs1"},
            {"from": "observation_stage.in_ready", "to": "top.obs_ready"},
            {"from": "observation_stage.out_valid", "to": "policy_score_core.in_valid"},
            {"from": "observation_stage.obs0_out", "to": "policy_score_core.obs0"},
            {"from": "observation_stage.obs1_out", "to": "policy_score_core.obs1"},
            {"from": "config_reg_bank.weight0", "to": "policy_score_core.weight0"},
            {"from": "config_reg_bank.weight1", "to": "policy_score_core.weight1"},
            {"from": "config_reg_bank.bias0", "to": "policy_score_core.bias0"},
            {"from": "config_reg_bank.bias1", "to": "policy_score_core.bias1"},
            {"from": "config_reg_bank.enable", "to": "policy_score_core.enable"},
            {"from": "policy_score_core.out_valid", "to": "action_select_core.in_valid"},
            {"from": "policy_score_core.score0", "to": "action_select_core.score0"},
            {"from": "policy_score_core.score1", "to": "action_select_core.score1"},
            {"from": "action_select_core.out_valid", "to": "stream_stage.in_valid"},
            {"from": "action_select_core.selected_action", "to": "stream_stage.selected_action"},
            {"from": "action_select_core.value_estimate", "to": "stream_stage.value_estimate"},
            {"from": "stream_stage.out_valid", "to": "top.action_valid"},
            {"from": "top.action_ready", "to": "stream_stage.out_ready"},
            {"from": "stream_stage.selected_action_out", "to": "top.selected_action"},
            {"from": "stream_stage.value_estimate_out", "to": "top.value_estimate"},
        ],
    },
    "composed_replay_sample_shell": {
        "topology_id": "t8_replay_sample_shell",
        "difficulty_tier": "T8",
        "submodules": [
            "host_sample_stage",
            "replay_store",
            "sample_pack_core",
            "sample_read_stage",
            "occupancy_counter",
        ],
        "nodes": [
            {"id": "host_stage", "component": "host_sample_stage"},
            {"id": "store", "component": "replay_store"},
            {"id": "pack", "component": "sample_pack_core"},
            {"id": "read_stage", "component": "sample_read_stage"},
            {"id": "occupancy", "component": "occupancy_counter"},
        ],
        "edges": [
            {"from": "top.host_valid", "to": "host_sample_stage.in_valid"},
            {"from": "top.host_state", "to": "host_sample_stage.state"},
            {"from": "top.host_action", "to": "host_sample_stage.action"},
            {"from": "top.host_reward", "to": "host_sample_stage.reward"},
            {"from": "top.host_next_state", "to": "host_sample_stage.next_state"},
            {"from": "top.host_done", "to": "host_sample_stage.done"},
            {"from": "host_sample_stage.in_ready", "to": "top.host_ready"},
            {"from": "host_sample_stage.out_valid", "to": "replay_store.write_valid"},
            {"from": "host_sample_stage.state_out", "to": "replay_store.write_state"},
            {"from": "host_sample_stage.action_out", "to": "replay_store.write_action"},
            {"from": "host_sample_stage.reward_out", "to": "replay_store.write_reward"},
            {"from": "host_sample_stage.next_state_out", "to": "replay_store.write_next_state"},
            {"from": "host_sample_stage.done_out", "to": "replay_store.write_done"},
            {"from": "replay_store.write_ready", "to": "host_sample_stage.out_ready"},
            {"from": "top.sample_ready", "to": "sample_read_stage.out_ready"},
            {"from": "sample_read_stage.read_ready", "to": "replay_store.read_ready"},
            {"from": "replay_store.read_valid", "to": "sample_read_stage.in_valid"},
            {"from": "replay_store.read_state", "to": "sample_pack_core.state"},
            {"from": "replay_store.read_action", "to": "sample_pack_core.action"},
            {"from": "replay_store.read_reward", "to": "sample_pack_core.reward"},
            {"from": "replay_store.read_next_state", "to": "sample_pack_core.next_state"},
            {"from": "replay_store.read_done", "to": "sample_pack_core.done"},
            {"from": "sample_pack_core.sample_state", "to": "sample_read_stage.sample_state"},
            {"from": "sample_pack_core.sample_action", "to": "sample_read_stage.sample_action"},
            {"from": "sample_pack_core.sample_reward", "to": "sample_read_stage.sample_reward"},
            {"from": "sample_pack_core.sample_next_state", "to": "sample_read_stage.sample_next_state"},
            {"from": "sample_pack_core.sample_done", "to": "sample_read_stage.sample_done"},
            {"from": "sample_read_stage.out_valid", "to": "top.sample_valid"},
            {"from": "sample_read_stage.sample_state_out", "to": "top.sample_state"},
            {"from": "sample_read_stage.sample_action_out", "to": "top.sample_action"},
            {"from": "sample_read_stage.sample_reward_out", "to": "top.sample_reward"},
            {"from": "sample_read_stage.sample_next_state_out", "to": "top.sample_next_state"},
            {"from": "sample_read_stage.sample_done_out", "to": "top.sample_done"},
            {"from": "replay_store.occupancy", "to": "occupancy_counter.occupancy_in"},
            {"from": "occupancy_counter.occupancy_out", "to": "top.occupancy"},
        ],
    },
    "composed_host_protocol_shell": {
        "topology_id": "t9_host_protocol_shell",
        "difficulty_tier": "T9",
        "submodules": [
            "axi_lite_write_ctrl",
            "axi_lite_read_ctrl",
            "control_reg_bank",
            "sample_stream_adapter",
            "irq_status",
        ],
        "nodes": [
            {"id": "write_ctrl", "component": "axi_lite_write_ctrl"},
            {"id": "read_ctrl", "component": "axi_lite_read_ctrl"},
            {"id": "regs", "component": "control_reg_bank"},
            {"id": "stream", "component": "sample_stream_adapter"},
            {"id": "irq", "component": "irq_status"},
        ],
        "edges": [
            {"from": "top.s_axi_awvalid", "to": "axi_lite_write_ctrl.awvalid"},
            {"from": "top.s_axi_awaddr", "to": "axi_lite_write_ctrl.awaddr"},
            {"from": "top.s_axi_wvalid", "to": "axi_lite_write_ctrl.wvalid"},
            {"from": "top.s_axi_wdata", "to": "axi_lite_write_ctrl.wdata"},
            {"from": "top.s_axi_wstrb", "to": "axi_lite_write_ctrl.wstrb"},
            {"from": "axi_lite_write_ctrl.awready", "to": "top.s_axi_awready"},
            {"from": "axi_lite_write_ctrl.wready", "to": "top.s_axi_wready"},
            {"from": "axi_lite_write_ctrl.bvalid", "to": "top.s_axi_bvalid"},
            {"from": "top.s_axi_bready", "to": "axi_lite_write_ctrl.bready"},
            {"from": "axi_lite_write_ctrl.write_valid", "to": "control_reg_bank.write_valid"},
            {"from": "axi_lite_write_ctrl.write_addr", "to": "control_reg_bank.write_addr"},
            {"from": "axi_lite_write_ctrl.write_data", "to": "control_reg_bank.write_data"},
            {"from": "top.s_axi_arvalid", "to": "axi_lite_read_ctrl.arvalid"},
            {"from": "top.s_axi_araddr", "to": "axi_lite_read_ctrl.araddr"},
            {"from": "axi_lite_read_ctrl.arready", "to": "top.s_axi_arready"},
            {"from": "axi_lite_read_ctrl.read_valid", "to": "control_reg_bank.read_valid"},
            {"from": "axi_lite_read_ctrl.read_addr", "to": "control_reg_bank.read_addr"},
            {"from": "control_reg_bank.read_data", "to": "top.s_axi_rdata"},
            {"from": "axi_lite_read_ctrl.rvalid", "to": "top.s_axi_rvalid"},
            {"from": "top.s_axi_rready", "to": "axi_lite_read_ctrl.rready"},
            {"from": "control_reg_bank.start_pulse", "to": "sample_stream_adapter.start"},
            {"from": "control_reg_bank.sample0", "to": "sample_stream_adapter.sample0"},
            {"from": "control_reg_bank.sample1", "to": "sample_stream_adapter.sample1"},
            {"from": "sample_stream_adapter.tvalid", "to": "top.m_axis_tvalid"},
            {"from": "top.m_axis_tready", "to": "sample_stream_adapter.tready"},
            {"from": "sample_stream_adapter.tdata", "to": "top.m_axis_tdata"},
            {"from": "sample_stream_adapter.tlast", "to": "top.m_axis_tlast"},
            {"from": "sample_stream_adapter.stream_done", "to": "control_reg_bank.stream_done"},
            {"from": "control_reg_bank.irq_state", "to": "irq_status.irq_in"},
            {"from": "irq_status.irq_out", "to": "top.irq"},
        ],
    },
    "composed_rl_accelerator_shell": {
        "topology_id": "t10_rl_accelerator_shell",
        "difficulty_tier": "T10",
        "submodules": [
            "host_config_bank",
            "sample_capture_stage",
            "policy_value_core",
            "td_update_core",
            "result_stream_stage",
        ],
        "nodes": [
            {"id": "config", "component": "host_config_bank"},
            {"id": "sample", "component": "sample_capture_stage"},
            {"id": "policy", "component": "policy_value_core"},
            {"id": "update", "component": "td_update_core"},
            {"id": "result", "component": "result_stream_stage"},
        ],
        "edges": [
            {"from": "top.cfg_valid", "to": "host_config_bank.cfg_valid"},
            {"from": "top.cfg_addr", "to": "host_config_bank.cfg_addr"},
            {"from": "top.cfg_data", "to": "host_config_bank.cfg_data"},
            {"from": "host_config_bank.cfg_ready", "to": "top.cfg_ready"},
            {"from": "top.sample_valid", "to": "sample_capture_stage.in_valid"},
            {"from": "sample_capture_stage.in_ready", "to": "top.sample_ready"},
            {"from": "top.obs0", "to": "sample_capture_stage.obs0"},
            {"from": "top.obs1", "to": "sample_capture_stage.obs1"},
            {"from": "top.reward", "to": "sample_capture_stage.reward"},
            {"from": "top.next_value", "to": "sample_capture_stage.next_value"},
            {"from": "top.done_in", "to": "sample_capture_stage.done_in"},
            {"from": "sample_capture_stage.out_valid", "to": "policy_value_core.in_valid"},
            {"from": "sample_capture_stage.obs0_out", "to": "policy_value_core.obs0"},
            {"from": "sample_capture_stage.obs1_out", "to": "policy_value_core.obs1"},
            {"from": "host_config_bank.weight0", "to": "policy_value_core.weight0"},
            {"from": "host_config_bank.bias0", "to": "policy_value_core.bias0"},
            {"from": "host_config_bank.weight1", "to": "policy_value_core.weight1"},
            {"from": "host_config_bank.bias1", "to": "policy_value_core.bias1"},
            {"from": "host_config_bank.enable", "to": "policy_value_core.enable"},
            {"from": "policy_value_core.out_valid", "to": "td_update_core.in_valid"},
            {"from": "policy_value_core.value_estimate", "to": "td_update_core.value_estimate"},
            {"from": "sample_capture_stage.reward_out", "to": "td_update_core.reward"},
            {"from": "sample_capture_stage.next_value_out", "to": "td_update_core.next_value"},
            {"from": "host_config_bank.alpha", "to": "td_update_core.alpha"},
            {"from": "td_update_core.out_valid", "to": "result_stream_stage.in_valid"},
            {"from": "policy_value_core.selected_action", "to": "result_stream_stage.selected_action"},
            {"from": "policy_value_core.value_estimate", "to": "result_stream_stage.value_estimate"},
            {"from": "td_update_core.updated_value", "to": "result_stream_stage.updated_value"},
            {"from": "sample_capture_stage.done_out", "to": "result_stream_stage.done_in"},
            {"from": "result_stream_stage.out_ready", "to": "sample_capture_stage.consume_ready"},
            {"from": "result_stream_stage.result_valid", "to": "top.result_valid"},
            {"from": "top.result_ready", "to": "result_stream_stage.result_ready"},
            {"from": "result_stream_stage.selected_action_out", "to": "top.selected_action"},
            {"from": "result_stream_stage.value_estimate_out", "to": "top.value_estimate"},
            {"from": "result_stream_stage.updated_value_out", "to": "top.updated_value"},
            {"from": "result_stream_stage.episode_done_out", "to": "top.episode_done"},
            {"from": "result_stream_stage.irq", "to": "top.irq"},
        ],
    },
    "composed_batch_rl_accelerator_shell": {
        "topology_id": "t11_batch_rl_accelerator_shell",
        "difficulty_tier": "T11",
        "submodules": [
            "batch_config_bank",
            "batch_sample_buffer",
            "dual_policy_value_core",
            "dual_td_update_core",
            "batch_result_stage",
        ],
        "nodes": [
            {"id": "config", "component": "batch_config_bank"},
            {"id": "batch", "component": "batch_sample_buffer"},
            {"id": "policy", "component": "dual_policy_value_core"},
            {"id": "update", "component": "dual_td_update_core"},
            {"id": "result", "component": "batch_result_stage"},
        ],
        "edges": [
            {"from": "top.cfg_valid", "to": "batch_config_bank.cfg_valid"},
            {"from": "top.cfg_addr", "to": "batch_config_bank.cfg_addr"},
            {"from": "top.cfg_data", "to": "batch_config_bank.cfg_data"},
            {"from": "batch_config_bank.cfg_ready", "to": "top.cfg_ready"},
            {"from": "top.batch_valid", "to": "batch_sample_buffer.in_valid"},
            {"from": "batch_sample_buffer.in_ready", "to": "top.batch_ready"},
            {"from": "top.obs0_a", "to": "batch_sample_buffer.obs0_a"},
            {"from": "top.obs1_a", "to": "batch_sample_buffer.obs1_a"},
            {"from": "top.reward_a", "to": "batch_sample_buffer.reward_a"},
            {"from": "top.next_value_a", "to": "batch_sample_buffer.next_value_a"},
            {"from": "top.done_a", "to": "batch_sample_buffer.done_a"},
            {"from": "top.obs0_b", "to": "batch_sample_buffer.obs0_b"},
            {"from": "top.obs1_b", "to": "batch_sample_buffer.obs1_b"},
            {"from": "top.reward_b", "to": "batch_sample_buffer.reward_b"},
            {"from": "top.next_value_b", "to": "batch_sample_buffer.next_value_b"},
            {"from": "top.done_b", "to": "batch_sample_buffer.done_b"},
            {"from": "batch_sample_buffer.out_valid", "to": "dual_policy_value_core.in_valid"},
            {"from": "batch_sample_buffer.obs0_a_out", "to": "dual_policy_value_core.obs0_a"},
            {"from": "batch_sample_buffer.obs1_a_out", "to": "dual_policy_value_core.obs1_a"},
            {"from": "batch_sample_buffer.obs0_b_out", "to": "dual_policy_value_core.obs0_b"},
            {"from": "batch_sample_buffer.obs1_b_out", "to": "dual_policy_value_core.obs1_b"},
            {"from": "batch_config_bank.weight0", "to": "dual_policy_value_core.weight0"},
            {"from": "batch_config_bank.bias0", "to": "dual_policy_value_core.bias0"},
            {"from": "batch_config_bank.weight1", "to": "dual_policy_value_core.weight1"},
            {"from": "batch_config_bank.bias1", "to": "dual_policy_value_core.bias1"},
            {"from": "batch_config_bank.enable", "to": "dual_policy_value_core.enable"},
            {"from": "dual_policy_value_core.out_valid", "to": "dual_td_update_core.in_valid"},
            {"from": "dual_policy_value_core.value_estimate_a", "to": "dual_td_update_core.value_estimate_a"},
            {"from": "dual_policy_value_core.value_estimate_b", "to": "dual_td_update_core.value_estimate_b"},
            {"from": "batch_sample_buffer.reward_a_out", "to": "dual_td_update_core.reward_a"},
            {"from": "batch_sample_buffer.next_value_a_out", "to": "dual_td_update_core.next_value_a"},
            {"from": "batch_sample_buffer.reward_b_out", "to": "dual_td_update_core.reward_b"},
            {"from": "batch_sample_buffer.next_value_b_out", "to": "dual_td_update_core.next_value_b"},
            {"from": "batch_config_bank.alpha", "to": "dual_td_update_core.alpha"},
            {"from": "dual_td_update_core.out_valid", "to": "batch_result_stage.in_valid"},
            {"from": "dual_policy_value_core.selected_action_a", "to": "batch_result_stage.selected_action_a"},
            {"from": "dual_policy_value_core.value_estimate_a", "to": "batch_result_stage.value_estimate_a"},
            {"from": "dual_td_update_core.updated_value_a", "to": "batch_result_stage.updated_value_a"},
            {"from": "dual_policy_value_core.selected_action_b", "to": "batch_result_stage.selected_action_b"},
            {"from": "dual_policy_value_core.value_estimate_b", "to": "batch_result_stage.value_estimate_b"},
            {"from": "dual_td_update_core.updated_value_b", "to": "batch_result_stage.updated_value_b"},
            {"from": "batch_sample_buffer.done_a_out", "to": "batch_result_stage.done_a"},
            {"from": "batch_sample_buffer.done_b_out", "to": "batch_result_stage.done_b"},
            {"from": "batch_result_stage.out_ready", "to": "batch_sample_buffer.consume_ready"},
            {"from": "batch_result_stage.result_valid", "to": "top.result_valid"},
            {"from": "top.result_ready", "to": "batch_result_stage.result_ready"},
            {"from": "batch_result_stage.selected_action_a_out", "to": "top.selected_action_a"},
            {"from": "batch_result_stage.value_estimate_a_out", "to": "top.value_estimate_a"},
            {"from": "batch_result_stage.updated_value_a_out", "to": "top.updated_value_a"},
            {"from": "batch_result_stage.selected_action_b_out", "to": "top.selected_action_b"},
            {"from": "batch_result_stage.value_estimate_b_out", "to": "top.value_estimate_b"},
            {"from": "batch_result_stage.updated_value_b_out", "to": "top.updated_value_b"},
            {"from": "batch_result_stage.batch_done_out", "to": "top.batch_done"},
            {"from": "batch_result_stage.irq", "to": "top.irq"},
        ],
    },
    "composed_replay_arbiter_shell": {
        "topology_id": "t12_replay_arbiter_shell",
        "difficulty_tier": "T12",
        "submodules": [
            "host_transition_packetizer",
            "replay_index_allocator",
            "replay_request_arbiter",
            "replay_memory_bank",
            "sample_packet_stage",
        ],
        "nodes": [
            {"id": "packetizer", "component": "host_transition_packetizer"},
            {"id": "allocator", "component": "replay_index_allocator"},
            {"id": "arbiter", "component": "replay_request_arbiter"},
            {"id": "memory", "component": "replay_memory_bank"},
            {"id": "sample_stage", "component": "sample_packet_stage"},
        ],
        "edges": [
            {"from": "top.host_valid", "to": "host_transition_packetizer.host_valid"},
            {"from": "top.host_state", "to": "host_transition_packetizer.host_state"},
            {"from": "top.host_action", "to": "host_transition_packetizer.host_action"},
            {"from": "top.host_reward", "to": "host_transition_packetizer.host_reward"},
            {"from": "top.host_next_state", "to": "host_transition_packetizer.host_next_state"},
            {"from": "top.host_done", "to": "host_transition_packetizer.host_done"},
            {"from": "host_transition_packetizer.host_ready", "to": "top.host_ready"},
            {"from": "host_transition_packetizer.packet_valid", "to": "replay_request_arbiter.write_valid"},
            {"from": "host_transition_packetizer.packet_state", "to": "replay_request_arbiter.write_state"},
            {"from": "host_transition_packetizer.packet_action", "to": "replay_request_arbiter.write_action"},
            {"from": "host_transition_packetizer.packet_reward", "to": "replay_request_arbiter.write_reward"},
            {"from": "host_transition_packetizer.packet_next_state", "to": "replay_request_arbiter.write_next_state"},
            {"from": "host_transition_packetizer.packet_done", "to": "replay_request_arbiter.write_done"},
            {"from": "replay_index_allocator.write_index", "to": "replay_request_arbiter.write_index"},
            {"from": "replay_index_allocator.occupancy", "to": "replay_request_arbiter.occupancy"},
            {"from": "top.sample_req_valid", "to": "replay_request_arbiter.read_req_valid"},
            {"from": "top.sample_index", "to": "replay_request_arbiter.sample_index"},
            {"from": "replay_request_arbiter.sample_req_ready", "to": "top.sample_req_ready"},
            {"from": "replay_request_arbiter.mem_write_valid", "to": "replay_memory_bank.write_valid"},
            {"from": "replay_request_arbiter.mem_write_addr", "to": "replay_memory_bank.write_addr"},
            {"from": "replay_request_arbiter.mem_write_state", "to": "replay_memory_bank.write_state"},
            {"from": "replay_request_arbiter.mem_write_action", "to": "replay_memory_bank.write_action"},
            {"from": "replay_request_arbiter.mem_write_reward", "to": "replay_memory_bank.write_reward"},
            {"from": "replay_request_arbiter.mem_write_next_state", "to": "replay_memory_bank.write_next_state"},
            {"from": "replay_request_arbiter.mem_write_done", "to": "replay_memory_bank.write_done"},
            {"from": "replay_request_arbiter.mem_read_valid", "to": "replay_memory_bank.read_valid"},
            {"from": "replay_request_arbiter.mem_read_addr", "to": "replay_memory_bank.read_addr"},
            {"from": "replay_request_arbiter.write_accepted", "to": "replay_index_allocator.write_accepted"},
            {"from": "replay_memory_bank.read_valid_out", "to": "sample_packet_stage.in_valid"},
            {"from": "replay_memory_bank.read_state", "to": "sample_packet_stage.sample_state"},
            {"from": "replay_memory_bank.read_action", "to": "sample_packet_stage.sample_action"},
            {"from": "replay_memory_bank.read_reward", "to": "sample_packet_stage.sample_reward"},
            {"from": "replay_memory_bank.read_next_state", "to": "sample_packet_stage.sample_next_state"},
            {"from": "replay_memory_bank.read_done", "to": "sample_packet_stage.sample_done"},
            {"from": "sample_packet_stage.sample_valid", "to": "top.sample_valid"},
            {"from": "top.sample_ready", "to": "sample_packet_stage.sample_ready"},
            {"from": "sample_packet_stage.sample_state_out", "to": "top.sample_state"},
            {"from": "sample_packet_stage.sample_action_out", "to": "top.sample_action"},
            {"from": "sample_packet_stage.sample_reward_out", "to": "top.sample_reward"},
            {"from": "sample_packet_stage.sample_next_state_out", "to": "top.sample_next_state"},
            {"from": "sample_packet_stage.sample_done_out", "to": "top.sample_done"},
            {"from": "sample_packet_stage.irq", "to": "top.irq"},
            {"from": "replay_index_allocator.occupancy", "to": "top.occupancy"},
            {"from": "replay_index_allocator.write_index", "to": "top.write_index"},
        ],
    },
}

class ProjectGenerator:
    """Generate minimal Verilog RTL project packages."""

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        if request.task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
        if request.width <= 0:
            raise ValueError("width must be positive")

        rtl_files = _rtl_files(request)
        files = {
            "system_his.json": _to_json(_system_his(request, platform, rtl_files)),
            "manifest.json": _to_json(_manifest(request, platform, rtl_files)),
            **rtl_files,
            "constraints/timing.sdc": _timing_sdc(platform),
            "sim/tb_top.v": _testbench(request),
            "reports/predicted_qor.json": _to_json(_predicted_qor(request, platform)),
        }
        return GeneratedProject(project_name=request.project_name, files=files)


def _to_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _system_his(
    request: ProjectRequest,
    platform: PlatformProfile,
    rtl_files: dict[str, str],
) -> dict[str, object]:
    interface = _interface(request, platform)
    architecture = _architecture(request)
    modules = _modules(interface, architecture, rtl_files)
    description = request.description or _default_description(request)
    predicted_resources = _resource_shape(request)
    top_module = str(architecture["top_module"])
    top_ports = _v12_ports(_top_ports(interface))
    components = _v12_components(modules)
    instances = _v12_instances(
        rtl_files,
        components,
        top_module,
        clock_name=str(interface["clock"]),
        reset_name=str(interface["reset"]),
    )
    data_flow = _v12_data_flow(request, top_ports, instances, components)
    return {
        "schema_version": "system-his-v1.2",
        "task_type": request.task_type,
        "project_name": request.project_name,
        "project": {
            "name": request.project_name,
            "description": description,
            "top": architecture["top_module"],
        },
        "clocks": [{"name": interface["clock"], "target_fmax_mhz": platform.clock_hz / 1_000_000}],
        "resets": [
            {
                "name": interface["reset"],
                "polarity": platform.reset_polarity,
                "kind": "async",
            }
        ],
        "intent": {
            "user_prompt": description,
            "design_goal": _expected_behavior(request),
            "assumptions": ["single synchronous clock", "no vendor-specific IP"],
        },
        "top": {
            "name": top_module,
            "parameters": [],
            "clocks": [{"name": interface["clock"], "target_fmax_mhz": platform.clock_hz / 1_000_000}],
            "resets": [
                {
                    "name": interface["reset"],
                    "polarity": platform.reset_polarity,
                    "kind": "async",
                }
            ],
            "ports": top_ports,
            "interfaces": [],
        },
        "state": _v12_state(request, top_module, instances),
        "components": components,
        "instances": instances,
        "data_flow": data_flow,
        "control_flow": _v12_control_flow(request, data_flow),
        "timing": {
            "primary_clock": interface["clock"],
            "target_fmax_mhz": platform.clock_hz / 1_000_000,
            "constraints": ["constraints/timing.sdc"],
        },
        "resources": {
            "optimization_goal": "area_first",
            "expected": {
                "lut": predicted_resources["lut"],
                "ff": predicted_resources["ff"],
                "bram": predicted_resources["bram"],
                "dsp": predicted_resources["dsp"],
            },
        },
        "verification": {
            "testbench": "sim/tb_top.v",
            "scenarios": ["reset", "nominal_operation"],
            "pass_condition": _test_pass_means(request),
            "checks": ["l0_contract", "l1_lint", "l2_self_checking_sim", "l3_synthesis"],
            "test_pass_means": _test_pass_means(request),
            "expected_behavior": _test_pass_means(request),
        },
        "artifacts": {
            "top_module": top_module,
            "rtl_sources": list(rtl_files.keys()),
            "testbench": "sim/tb_top.v",
            "constraints": ["constraints/timing.sdc"],
            "manifest": "manifest.json",
            "predicted_qor": "reports/predicted_qor.json",
        },
        # Transitional metadata retained for runner/export compatibility while
        # the canonical schema migrates from v1.1 to v1.2.
        "system": {"description": description},
        "interface": interface,
        "architecture": architecture,
        "modules": modules,
        "connections": _connections(architecture, rtl_files, modules),
        "top_ports": _top_ports(interface),
        "qor_intent": {"resources": predicted_resources},
        "platform": {
            "name": platform.name,
            "vendor": platform.vendor,
            "family": platform.family,
            "part": platform.part,
            "board": platform.board,
            "toolchain": platform.toolchain,
            "clock_hz": platform.clock_hz,
        },
    }


def _v12_ports(ports: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "name": port["name"],
            "dir": port.get("direction", port.get("dir")),
            "width": port["width"],
        }
        for port in ports
    ]


def _v12_components(modules: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "name": module["name"],
            "semantic_kind": _v12_semantic_kind(str(module["name"]), str(module.get("role", ""))),
            "source": module["source"],
            "parameters": [
                {"name": name, "default": value}
                for name, value in dict(module.get("parameters", {})).items()
            ],
            "ports": _v12_ports(module["ports"]),
            "intent": module.get("intent") or _module_intent(str(module["name"])),
        }
        for module in modules
    ]


def _v12_semantic_kind(module_name: str, role: str) -> str:
    if role == "top":
        return "top_integration"
    name = module_name.lower()
    for term in (
        "buffer",
        "fifo",
        "join",
        "fork",
        "accumulator",
        "counter",
        "fsm",
        "ram",
        "spi",
        "pwm",
        "mac",
        "stage",
        "gate",
    ):
        if term in name:
            return term
    return "rtl_component"


def _v12_instances(
    rtl_files: dict[str, str],
    components: list[dict[str, object]],
    top_module: str,
    *,
    clock_name: str,
    reset_name: str,
) -> list[dict[str, object]]:
    component_names = {str(component["name"]) for component in components if str(component["name"]) != top_module}
    components_by_name = {str(component["name"]): component for component in components}
    instance_ports = _top_instance_ports(rtl_files["rtl/top.v"], component_names)
    instances: dict[str, dict[str, object]] = {}
    for endpoint in instance_ports:
        instance_name = endpoint["instance"]
        component = components_by_name.get(str(endpoint["module"]), {})
        instances.setdefault(
            instance_name,
            {
                "name": instance_name,
                "component": endpoint["module"],
                "parameter_values": _v12_component_parameter_values(component),
                "clock": clock_name,
                "reset": reset_name,
                "owns_state": [],
            },
        )
    return list(instances.values())


def _v12_component_parameter_values(component: dict[str, object]) -> dict[str, object]:
    values: dict[str, object] = {}
    parameters = component.get("parameters", [])
    if not isinstance(parameters, list):
        return values
    for parameter in parameters:
        if not isinstance(parameter, dict):
            continue
        name = str(parameter.get("name", "")).strip()
        if name:
            values[name] = parameter.get("default")
    return values


def _v12_state(
    request: ProjectRequest,
    top_module: str,
    instances: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    owner = str(instances[0]["name"]) if instances else top_module
    registers: list[dict[str, object]] = []
    counters: list[dict[str, object]] = []
    fsms: list[dict[str, object]] = []
    buffers: list[dict[str, object]] = []
    memories: list[dict[str, object]] = []
    if request.task_type == "counter":
        counters.append({"name": "count", "owner": top_module, "width": request.width})
    elif request.task_type == "fifo":
        buffers.append({"name": "fifo_storage", "owner": top_module, "width": request.width, "depth": 4})
        counters.extend(
            [
                {"name": "wr_ptr", "owner": top_module, "width": 2},
                {"name": "rd_ptr", "owner": top_module, "width": 2},
                {"name": "count", "owner": top_module, "width": 3},
            ]
        )
    elif request.task_type == "simple_fsm":
        fsms.append(
            {
                "name": "top_fsm",
                "owner": owner,
                "states": ["IDLE", "RUN", "DONE"],
                "initial": "IDLE",
                "reset_state": "IDLE",
            }
        )
        registers.append({"name": "state_value", "owner": top_module, "width": max(2, request.width)})
    elif request.task_type == "ram_read_write":
        memories.append({"name": "mem", "owner": top_module, "width": request.width, "depth": 4})
        registers.append({"name": "rdata", "owner": top_module, "width": request.width})
    elif request.task_type == "composed_vector_mac_pipeline":
        mac_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "vector_mac_core"),
            owner,
        )
        registers.extend(
            [
                {"name": "accumulator", "owner": mac_owner, "width": request.width * 2},
                {"name": "pending_score", "owner": mac_owner, "width": request.width * 2},
            ]
        )
        counters.append({"name": "vector_index", "owner": mac_owner, "width": 2})
    elif request.task_type == "composed_td_update_core":
        input_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "td_input_stage"),
            owner,
        )
        update_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "td_update_core"),
            owner,
        )
        registers.extend(
            [
                {"name": "captured_reward", "owner": input_owner, "width": request.width},
                {"name": "captured_value", "owner": input_owner, "width": request.width},
                {"name": "captured_next_value", "owner": input_owner, "width": request.width},
                {"name": "td_error", "owner": update_owner, "width": request.width},
                {"name": "updated_value", "owner": update_owner, "width": request.width},
            ]
        )
    elif request.task_type == "composed_policy_value_shell":
        config_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "config_reg_bank"),
            owner,
        )
        observation_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "observation_stage"),
            owner,
        )
        output_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "stream_stage"),
            owner,
        )
        registers.extend(
            [
                {"name": "weight0", "owner": config_owner, "width": request.width},
                {"name": "weight1", "owner": config_owner, "width": request.width},
                {"name": "bias0", "owner": config_owner, "width": request.width},
                {"name": "bias1", "owner": config_owner, "width": request.width},
                {"name": "enable", "owner": config_owner, "width": 1},
                {"name": "captured_obs0", "owner": observation_owner, "width": request.width},
                {"name": "captured_obs1", "owner": observation_owner, "width": request.width},
                {"name": "selected_action", "owner": output_owner, "width": 1},
                {"name": "value_estimate", "owner": output_owner, "width": request.width},
            ]
        )
    elif request.task_type == "composed_replay_sample_shell":
        host_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "host_sample_stage"),
            owner,
        )
        store_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "replay_store"),
            owner,
        )
        read_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "sample_read_stage"),
            owner,
        )
        registers.extend(
            [
                {"name": "staged_state", "owner": host_owner, "width": request.width},
                {"name": "staged_reward", "owner": host_owner, "width": request.width},
                {"name": "staged_next_state", "owner": host_owner, "width": request.width},
                {"name": "write_ptr", "owner": store_owner, "width": 2},
                {"name": "read_ptr", "owner": store_owner, "width": 2},
                {"name": "occupancy", "owner": store_owner, "width": 3},
                {"name": "sample_state", "owner": read_owner, "width": request.width},
                {"name": "sample_reward", "owner": read_owner, "width": request.width},
                {"name": "sample_next_state", "owner": read_owner, "width": request.width},
            ]
        )
        buffers.append({"name": "replay_entries", "owner": store_owner, "width": request.width * 3 + 2, "depth": 4})
    elif request.task_type == "composed_host_protocol_shell":
        reg_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "control_reg_bank"),
            owner,
        )
        registers.extend(
            [
                {"name": "ctrl", "owner": reg_owner, "width": request.width},
                {"name": "sample0", "owner": reg_owner, "width": request.width},
                {"name": "sample1", "owner": reg_owner, "width": request.width},
                {"name": "busy", "owner": reg_owner, "width": 1},
                {"name": "done", "owner": reg_owner, "width": 1},
                {"name": "irq_state", "owner": reg_owner, "width": 1},
            ]
        )
    elif request.task_type == "composed_rl_accelerator_shell":
        config_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "host_config_bank"),
            owner,
        )
        sample_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "sample_capture_stage"),
            owner,
        )
        result_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "result_stream_stage"),
            owner,
        )
        registers.extend(
            [
                {"name": "weight0", "owner": config_owner, "width": request.width},
                {"name": "bias0", "owner": config_owner, "width": request.width},
                {"name": "weight1", "owner": config_owner, "width": request.width},
                {"name": "bias1", "owner": config_owner, "width": request.width},
                {"name": "alpha", "owner": config_owner, "width": request.width},
                {"name": "enable", "owner": config_owner, "width": 1},
                {"name": "captured_obs0", "owner": sample_owner, "width": request.width},
                {"name": "captured_obs1", "owner": sample_owner, "width": request.width},
                {"name": "captured_reward", "owner": sample_owner, "width": request.width},
                {"name": "captured_next_value", "owner": sample_owner, "width": request.width},
                {"name": "captured_done", "owner": sample_owner, "width": 1},
                {"name": "selected_action", "owner": result_owner, "width": 1},
                {"name": "value_estimate", "owner": result_owner, "width": request.width},
                {"name": "updated_value", "owner": result_owner, "width": request.width},
                {"name": "episode_done", "owner": result_owner, "width": 1},
                {"name": "irq_state", "owner": result_owner, "width": 1},
            ]
        )
    elif request.task_type == "composed_batch_rl_accelerator_shell":
        config_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "batch_config_bank"),
            owner,
        )
        batch_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "batch_sample_buffer"),
            owner,
        )
        result_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "batch_result_stage"),
            owner,
        )
        registers.extend(
            [
                {"name": "weight0", "owner": config_owner, "width": request.width},
                {"name": "bias0", "owner": config_owner, "width": request.width},
                {"name": "weight1", "owner": config_owner, "width": request.width},
                {"name": "bias1", "owner": config_owner, "width": request.width},
                {"name": "alpha", "owner": config_owner, "width": request.width},
                {"name": "enable", "owner": config_owner, "width": 1},
                {"name": "captured_obs0_a", "owner": batch_owner, "width": request.width},
                {"name": "captured_obs1_a", "owner": batch_owner, "width": request.width},
                {"name": "captured_reward_a", "owner": batch_owner, "width": request.width},
                {"name": "captured_next_value_a", "owner": batch_owner, "width": request.width},
                {"name": "captured_done_a", "owner": batch_owner, "width": 1},
                {"name": "captured_obs0_b", "owner": batch_owner, "width": request.width},
                {"name": "captured_obs1_b", "owner": batch_owner, "width": request.width},
                {"name": "captured_reward_b", "owner": batch_owner, "width": request.width},
                {"name": "captured_next_value_b", "owner": batch_owner, "width": request.width},
                {"name": "captured_done_b", "owner": batch_owner, "width": 1},
                {"name": "selected_action_a", "owner": result_owner, "width": 1},
                {"name": "value_estimate_a", "owner": result_owner, "width": request.width},
                {"name": "updated_value_a", "owner": result_owner, "width": request.width},
                {"name": "selected_action_b", "owner": result_owner, "width": 1},
                {"name": "value_estimate_b", "owner": result_owner, "width": request.width},
                {"name": "updated_value_b", "owner": result_owner, "width": request.width},
                {"name": "batch_done", "owner": result_owner, "width": 1},
                {"name": "irq_state", "owner": result_owner, "width": 1},
            ]
        )
    elif request.task_type == "composed_replay_arbiter_shell":
        allocator_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "replay_index_allocator"),
            owner,
        )
        memory_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "replay_memory_bank"),
            owner,
        )
        sample_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "sample_packet_stage"),
            owner,
        )
        registers.extend(
            [
                {"name": "write_index", "owner": allocator_owner, "width": 2},
                {"name": "occupancy", "owner": allocator_owner, "width": 3},
                {"name": "sample_state", "owner": sample_owner, "width": request.width},
                {"name": "sample_reward", "owner": sample_owner, "width": request.width},
                {"name": "sample_next_state", "owner": sample_owner, "width": request.width},
                {"name": "sample_action", "owner": sample_owner, "width": 1},
                {"name": "sample_done", "owner": sample_owner, "width": 1},
                {"name": "irq_state", "owner": sample_owner, "width": 1},
            ]
        )
        memories.append({"name": "replay_entries", "owner": memory_owner, "width": request.width * 3 + 2, "depth": 4})
    return {
        "registers": registers,
        "counters": counters,
        "fsms": fsms,
        "buffers": buffers,
        "memories": memories,
    }


def _v12_data_flow(
    request: ProjectRequest,
    top_ports: list[dict[str, object]],
    instances: list[dict[str, object]],
    components: list[dict[str, object]],
) -> list[dict[str, object]]:
    if instances:
        instance_ports = _component_ports_by_instance(instances, components)
        top_input = _primary_top_endpoint(top_ports, "input")
        top_output = _primary_top_endpoint(top_ports, "output")
        flows = []
        for instance_name, ports in instance_ports.items():
            input_ports = [name for name, direction in ports.items() if direction == "input" and name not in {"clk", "rst_n"}]
            output_ports = [name for name, direction in ports.items() if direction == "output"]
            if input_ports and output_ports:
                protocol = "valid_ready" if any("valid" in name or "ready" in name for name in input_ports + output_ports) else "register"
                path = [f"{instance_name}.{input_ports[0]}", f"{instance_name}.{output_ports[0]}"]
                if top_input:
                    path.insert(0, top_input)
                if top_output:
                    path.append(top_output)
                flow: dict[str, object] = {
                    "name": f"{instance_name}_primary_path",
                    "path": path,
                    "payload": {"name": "primary_payload", "width": request.width},
                    "protocol": protocol,
                }
                if protocol == "valid_ready":
                    flow["timing"] = {
                        "latency_cycles": 1,
                        "initiation_interval": 1,
                        "throughput": "one transfer per cycle when ready is asserted",
                    }
                flows.append(flow)
        return flows
    inputs = [str(port["name"]) for port in top_ports if port.get("dir") == "input" and port["name"] not in {"clk", "rst_n"}]
    outputs = [str(port["name"]) for port in top_ports if port.get("dir") == "output"]
    if not inputs or not outputs:
        return []
    flow = {
        "name": f"{request.task_type}_primary_path",
        "path": [f"top.{inputs[0]}", f"top.{outputs[0]}"],
        "payload": {"name": "primary_payload", "width": request.width},
        "protocol": "valid_ready" if any("valid" in name or "ready" in name for name in inputs + outputs) else "register",
    }
    if request.task_type in {"fifo", "simple_fsm", "ram_read_write"}:
        flow["timing"] = {"latency_cycles": 1, "initiation_interval": 1, "throughput": "one operation per cycle when enabled"}
    return [flow]


def _primary_top_endpoint(top_ports: list[dict[str, object]], direction: str) -> str:
    candidates = [
        str(port.get("name", ""))
        for port in top_ports
        if port.get("dir") == direction and str(port.get("name", "")) not in {"clk", "rst_n"}
    ]
    if not candidates:
        return ""
    preferred_terms = (
        ("data", "payload", "sample", "din", "wdata", "a", "b", "start", "en", "valid")
        if direction == "input"
        else ("data", "payload", "result", "sum", "count", "rdata", "tx", "pwm", "valid", "ready")
    )
    for term in preferred_terms:
        for name in candidates:
            if term in name:
                return f"top.{name}"
    return f"top.{candidates[0]}"


def _component_ports_by_instance(
    instances: list[dict[str, object]],
    components: list[dict[str, object]],
) -> dict[str, dict[str, str]]:
    components_by_name = {str(component["name"]): component for component in components}
    ports_by_instance: dict[str, dict[str, str]] = {}
    for instance in instances:
        component = components_by_name.get(str(instance["component"]), {})
        ports_by_instance[str(instance["name"])] = {
            str(port["name"]): str(port.get("dir", port.get("direction", "")))
            for port in component.get("ports", [])
            if isinstance(port, dict)
        }
    return ports_by_instance


def _v12_control_flow(request: ProjectRequest, data_flow: list[dict[str, object]]) -> list[dict[str, object]]:
    if request.task_type == "simple_fsm":
        return [
            {
                "name": "reset_to_idle",
                "kind": "fsm_transition",
                "fsm": "top_fsm",
                "from": "DONE",
                "to": "IDLE",
                "when": {"signal": "top.start", "op": "==", "value": 0},
                "related_state": ["top_fsm.state"],
                "related_flows": [],
            },
            {
                "name": "start_run",
                "kind": "fsm_transition",
                "fsm": "top_fsm",
                "from": "IDLE",
                "to": "RUN",
                "when": {"signal": "top.start", "op": "==", "value": 1},
                "related_state": ["top_fsm.state"],
                "related_flows": [],
            },
            {
                "name": "run_done",
                "kind": "fsm_transition",
                "fsm": "top_fsm",
                "from": "RUN",
                "to": "DONE",
                "when": {"signal": "top.state_value", "op": ">", "value": 2},
                "related_state": ["top_fsm.state", "top.state_value"],
                "related_flows": ["simple_fsm_primary_path"],
            },
        ]
    rules: list[dict[str, object]] = [
        {
            "name": "reset_state",
            "kind": "reset_rule",
            "condition": "rst_n == 0",
            "effects": ["reset architectural state"],
            "related_state": [],
            "related_flows": [],
        }
    ]
    if request.task_type in {
        "streaming_valid_ready",
        "composed_stream_accumulator",
        "composed_stream_fork",
        "composed_dual_stream_join",
        "composed_vector_mac_pipeline",
        "composed_td_update_core",
        "composed_policy_value_shell",
        "composed_replay_sample_shell",
        "composed_host_protocol_shell",
        "composed_rl_accelerator_shell",
        "composed_batch_rl_accelerator_shell",
        "composed_replay_arbiter_shell",
    }:
        flow_names = [str(flow["name"]) for flow in data_flow]
        rules.extend(
            [
                {
                    "name": "valid_ready_transfer",
                    "kind": "handshake_rule",
                    "condition": "valid && ready",
                    "effects": ["advance each ready/valid flow by one payload"],
                    "related_state": [],
                    "related_flows": flow_names,
                },
                {
                    "name": "backpressure_hold",
                    "kind": "stall_rule",
                    "condition": "valid && !ready",
                    "effects": ["hold payload and valid state until downstream ready"],
                    "related_state": [],
                    "related_flows": flow_names,
                },
            ]
        )
    return rules


def _modules(
    interface: dict[str, object],
    architecture: dict[str, object],
    rtl_files: dict[str, str],
) -> list[dict[str, object]]:
    module_sources = _module_sources(rtl_files)
    module_ports = _module_ports(rtl_files)
    module_parameters = _top_instance_parameters(rtl_files["rtl/top.v"], set(module_sources) - {str(architecture["top_module"])})
    top_module = str(architecture["top_module"])
    clock_name = str(interface["clock"])
    reset_name = str(interface["reset"])
    modules = [
        {
            "name": top_module,
            "role": "top",
            "source": module_sources[top_module],
            "clock": clock_name,
            "reset": reset_name,
            "parameters": {},
            "params": [],
            "ports": _top_ports(interface),
            "intent": "top-level integration wrapper for the generated RTL project",
        }
    ]
    for submodule in architecture["submodules"]:
        parameters = module_parameters.get(str(submodule), {})
        modules.append(
            {
                "name": submodule,
                "role": "submodule",
                "source": module_sources[str(submodule)],
                "clock": clock_name,
                "reset": reset_name,
                "parameters": parameters,
                "params": _params_from_parameters(parameters),
                "ports": module_ports[str(submodule)],
                "intent": _module_intent(str(submodule)),
            }
        )
    return modules


def _params_from_parameters(parameters: dict[str, object]) -> list[dict[str, object]]:
    return [{"name": name, "value": value} for name, value in parameters.items()]


def _module_intent(module_name: str) -> str:
    words = module_name.replace("_", " ")
    return f"{words} component in the generated RTL project"


def _top_ports(interface: dict[str, object]) -> list[dict[str, object]]:
    ports: list[dict[str, object]] = []
    for direction, his_direction in (("inputs", "input"), ("outputs", "output")):
        for port in interface[direction]:
            ports.append(
                {
                    "name": port["name"],
                    "direction": his_direction,
                    "width": port["width"],
                }
            )
    return ports


def _connections(
    architecture: dict[str, object],
    rtl_files: dict[str, str],
    modules: list[dict[str, object]],
) -> list[dict[str, object]]:
    top_module = str(architecture["top_module"])
    ports_by_module = {
        str(module["name"]): {str(port["name"]): str(port["direction"]) for port in module["ports"]}
        for module in modules
    }
    widths_by_module = {
        str(module["name"]): {str(port["name"]): port["width"] for port in module["ports"]}
        for module in modules
    }
    top_ports = ports_by_module.get(top_module, {})
    instance_ports = _top_instance_ports(rtl_files["rtl/top.v"], set(ports_by_module) - {top_module})
    by_signal: dict[str, list[dict[str, str]]] = {}
    for item in instance_ports:
        by_signal.setdefault(item["signal"], []).append(item)

    connections: list[dict[str, object]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for signal, endpoints in by_signal.items():
        top_direction = top_ports.get(signal)
        sinks = [item for item in endpoints if ports_by_module[item["module"]].get(item["port"]) == "input"]
        drivers = [item for item in endpoints if ports_by_module[item["module"]].get(item["port"]) == "output"]

        if top_direction == "input":
            for sink in sinks:
                _append_connection(connections, seen, signal, {"module": top_module, "port": signal}, sink, widths_by_module)
        for driver in drivers:
            if top_direction == "output":
                _append_connection(connections, seen, signal, driver, {"module": top_module, "port": signal}, widths_by_module)
            for sink in sinks:
                _append_connection(connections, seen, signal, driver, sink, widths_by_module)
    return connections


def _module_sources(rtl_files: dict[str, str]) -> dict[str, str]:
    module_sources: dict[str, str] = {}
    for source, content in rtl_files.items():
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith("module "):
                continue
            name = stripped.split()[1].split("(")[0]
            module_sources[name] = source
    return module_sources


def _module_ports(rtl_files: dict[str, str]) -> dict[str, list[dict[str, object]]]:
    ports: dict[str, list[dict[str, object]]] = {}
    for content in rtl_files.values():
        for module_name in re.findall(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", content, re.MULTILINE):
            ports[module_name] = _parse_module_ports(content, module_name)
    return ports


def _parse_module_ports(content: str, module_name: str) -> list[dict[str, object]]:
    body = _module_port_body(content, module_name)
    if body is None:
        return []
    ports: list[dict[str, object]] = []
    for declaration in _split_port_declarations(body):
        match = re.search(
            r"\b(input|output|inout)\b\s+(?:wire|reg\s+|reg|wire\s+)?\s*(?:signed\s+)?(\[[^\]]+\])?\s*([A-Za-z_][A-Za-z0-9_$]*)",
            declaration,
        )
        if match is None:
            continue
        ports.append(
            {
                "name": match.group(3),
                "direction": match.group(1),
                "width": _port_width(match.group(2)),
            }
        )
    return ports


def _module_port_body(content: str, module_name: str) -> str | None:
    match = re.search(rf"\bmodule\s+{re.escape(module_name)}\b", content)
    if match is None:
        return None
    index = match.end()
    while index < len(content) and content[index].isspace():
        index += 1
    if content.startswith("#", index):
        hash_index = index + 1
        while hash_index < len(content) and content[hash_index].isspace():
            hash_index += 1
        if hash_index < len(content) and content[hash_index] == "(":
            index = _matching_paren(content, hash_index) + 1
    while index < len(content) and content[index].isspace():
        index += 1
    if index >= len(content) or content[index] != "(":
        return None
    end = _matching_paren(content, index)
    return content[index + 1 : end]


def _matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unbalanced parentheses in generated Verilog")


def _split_port_declarations(body: str) -> list[str]:
    declarations: list[str] = []
    for part in body.split(","):
        stripped = " ".join(part.strip().split())
        if stripped:
            declarations.append(stripped)
    return declarations


def _port_width(range_text: str | None) -> int | str:
    if range_text is None:
        return 1
    numeric = re.fullmatch(r"\[(\d+):0\]", range_text.strip())
    if numeric is not None:
        return int(numeric.group(1)) + 1
    return range_text.strip()


def _top_instance_ports(top_rtl: str, submodules: set[str]) -> list[dict[str, str]]:
    endpoints: list[dict[str, str]] = []
    pattern = re.compile(
        r"\b(?P<module>[A-Za-z_][A-Za-z0-9_$]*)\b\s*(?:#\s*\(.*?\)\s*)?"
        r"(?P<instance>u_[A-Za-z_][A-Za-z0-9_$]*)\s*\((?P<ports>.*?)\)\s*;",
        re.DOTALL,
    )
    for match in pattern.finditer(top_rtl):
        module_name = match.group("module")
        if module_name not in submodules:
            continue
        instance = match.group("instance")
        for port, signal in re.findall(r"\.([A-Za-z_][A-Za-z0-9_$]*)\s*\(\s*([A-Za-z_][A-Za-z0-9_$]*)\s*\)", match.group("ports")):
            endpoints.append({"module": module_name, "instance": instance, "port": port, "signal": signal})
    return endpoints


def _top_instance_parameters(top_rtl: str, submodules: set[str]) -> dict[str, dict[str, object]]:
    parameters: dict[str, dict[str, object]] = {}
    pattern = re.compile(
        r"\b(?P<module>[A-Za-z_][A-Za-z0-9_$]*)\b\s*"
        r"(?:#\s*\((?P<params>.*?)\)\s*)?"
        r"(?P<instance>u_[A-Za-z_][A-Za-z0-9_$]*)\s*\(",
        re.DOTALL,
    )
    for match in pattern.finditer(top_rtl):
        module_name = match.group("module")
        if module_name not in submodules:
            continue
        raw_params = match.group("params") or ""
        parsed: dict[str, object] = {}
        for name, value in re.findall(r"\.([A-Za-z_][A-Za-z0-9_$]*)\s*\(\s*([^)]+?)\s*\)", raw_params):
            parsed[name] = _parameter_value(value)
        parameters[module_name] = parsed
    return parameters


def _parameter_value(value: str) -> object:
    stripped = value.strip()
    if re.fullmatch(r"\d+", stripped):
        return int(stripped)
    return stripped


def _append_connection(
    connections: list[dict[str, object]],
    seen: set[tuple[str, str, str, str, str]],
    signal: str,
    source: dict[str, str],
    target: dict[str, str],
    widths_by_module: dict[str, dict[str, object]],
) -> None:
    key = (signal, source["module"], source["port"], target["module"], target["port"])
    if key in seen:
        return
    seen.add(key)
    connections.append(
        {
            "from": _connection_endpoint(source),
            "to": _connection_endpoint(target),
            "signal": signal,
            "kind": "port_connection",
            "protocol": _connection_protocol(source["port"], target["port"]),
            "width": _connection_width(source, target, widths_by_module),
            "cdc": False,
        }
    )


def _connection_protocol(source_port: str, target_port: str) -> str:
    port_text = f"{source_port} {target_port}"
    if any(token in port_text for token in ("valid", "ready")):
        return "valid_ready"
    return "register"


def _connection_width(
    source: dict[str, str],
    target: dict[str, str],
    widths_by_module: dict[str, dict[str, object]],
) -> object:
    source_width = widths_by_module.get(source["module"], {}).get(source["port"])
    if source_width is not None:
        return source_width
    return widths_by_module.get(target["module"], {}).get(target["port"], 1)


def _connection_endpoint(endpoint: dict[str, str]) -> dict[str, str]:
    payload = {"module": endpoint["module"], "port": endpoint["port"]}
    if "instance" in endpoint:
        payload["instance"] = endpoint["instance"]
    return payload


def _architecture(request: ProjectRequest) -> dict[str, object]:
    submodules = {
        "counter": [],
        "fifo": [],
        "simple_fsm": [],
        "ram_read_write": [],
        "uart_tx": ["baud_tick_gen", "uart_tx_core"],
        "spi_master": ["clock_divider", "spi_master_core"],
        "pwm_controller": ["pwm_timer", "pwm_channel"],
        "fir_filter": ["mac_unit", "fir_filter_core"],
        "streaming_valid_ready": ["skid_buffer", "stream_stage"],
        "matrix_vector_mac": ["vector_rom", "mac_unit", "dot_product_engine"],
    }
    if request.task_type in COMPONENT_TOPOLOGIES:
        submodules[request.task_type] = list(COMPONENT_TOPOLOGIES[request.task_type]["submodules"])
    architecture = {
        "style": "multi_module" if submodules[request.task_type] else "single_module",
        "top_module": "top",
        "submodules": submodules[request.task_type],
    }
    if request.task_type in COMPONENT_TOPOLOGIES:
        topology = COMPONENT_TOPOLOGIES[request.task_type]
        architecture.update(
            {
                "generator": "component_topology",
                "topology_id": topology["topology_id"],
                "difficulty_tier": topology["difficulty_tier"],
                "component_library": COMPONENT_LIBRARY_ID,
                "topology": {
                    "nodes": topology["nodes"],
                    "edges": topology["edges"],
                },
            }
        )
    return architecture


def _manifest(
    request: ProjectRequest,
    platform: PlatformProfile,
    rtl_files: dict[str, str] | None = None,
) -> dict[str, object]:
    sources = list((rtl_files or {"rtl/top.v": ""}).keys())
    return {
        "project_name": request.project_name,
        "top_module": "top",
        "language": "verilog",
        "target": {
            "vendor": platform.vendor,
            "family": platform.family,
            "part": platform.part,
            "board": platform.board,
            "toolchain": platform.toolchain,
        },
        "sources": sources,
        "constraints": {"timing": "constraints/timing.sdc"},
        "simulation": {"testbench": "sim/tb_top.v", "type": "self_checking"},
        "reports": {"predicted_qor": "reports/predicted_qor.json"},
        "clock": {"name": "clk", "frequency_hz": platform.clock_hz},
        "reset": {"name": "rst_n", "polarity": platform.reset_polarity},
    }


def _counter_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire en,
            output reg [{msb}:0] count
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              count <= {width}'d0;
            end else if (en) begin
              count <= count + {{ {width - 1}'d0, 1'b1 }};
            end
          end

        endmodule
        """
    )


def _rtl_files(request: ProjectRequest) -> dict[str, str]:
    if request.task_type == "counter":
        return {"rtl/top.v": _counter_rtl(request.width)}
    if request.task_type == "fifo":
        return {"rtl/top.v": _fifo_rtl(request.width)}
    if request.task_type == "simple_fsm":
        return {"rtl/top.v": _simple_fsm_rtl(max(2, request.width))}
    if request.task_type == "ram_read_write":
        return {"rtl/top.v": _ram_read_write_rtl(request.width)}
    if request.task_type == "uart_tx":
        return _uart_tx_rtl_files(request.width)
    if request.task_type == "spi_master":
        return _spi_master_rtl_files(request.width)
    if request.task_type == "pwm_controller":
        return _pwm_controller_rtl_files(request.width)
    if request.task_type == "fir_filter":
        return _fir_filter_rtl_files(request.width)
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_rtl_files(request.width)
    if request.task_type == "matrix_vector_mac":
        return _matrix_vector_mac_rtl_files(request.width)
    if request.task_type == "composed_event_counter":
        return _composed_event_counter_rtl_files(request.width)
    if request.task_type == "composed_stream_accumulator":
        return _composed_stream_accumulator_rtl_files(request.width)
    if request.task_type == "composed_stream_fork":
        return _composed_stream_fork_rtl_files(request.width)
    if request.task_type == "composed_dual_stream_join":
        return _composed_dual_stream_join_rtl_files(request.width)
    if request.task_type == "composed_vector_mac_pipeline":
        return _composed_vector_mac_pipeline_rtl_files(request.width)
    if request.task_type == "composed_td_update_core":
        return _composed_td_update_core_rtl_files(request.width)
    if request.task_type == "composed_policy_value_shell":
        return _composed_policy_value_shell_rtl_files(request.width)
    if request.task_type == "composed_replay_sample_shell":
        return _composed_replay_sample_shell_rtl_files(request.width)
    if request.task_type == "composed_host_protocol_shell":
        return _composed_host_protocol_shell_rtl_files(request.width)
    if request.task_type == "composed_rl_accelerator_shell":
        return _composed_rl_accelerator_shell_rtl_files(request.width)
    if request.task_type == "composed_batch_rl_accelerator_shell":
        return _composed_batch_rl_accelerator_shell_rtl_files(request.width)
    if request.task_type == "composed_replay_arbiter_shell":
        return _composed_replay_arbiter_shell_rtl_files(request.width)
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")


def _rtl(request: ProjectRequest) -> str:
    return _rtl_files(request)["rtl/top.v"]


def _timing_sdc(platform: PlatformProfile) -> str:
    period_ns = 1_000_000_000 / platform.clock_hz
    return f"create_clock -name clk -period {period_ns:.3f} [get_ports clk]\n"


def _testbench(request: ProjectRequest) -> str:
    if request.task_type == "counter":
        return _counter_testbench(request.width)
    if request.task_type == "fifo":
        return _fifo_testbench(request.width)
    if request.task_type == "simple_fsm":
        return _simple_fsm_testbench(max(2, request.width))
    if request.task_type == "ram_read_write":
        return _ram_read_write_testbench(request.width)
    if request.task_type == "uart_tx":
        return _uart_tx_testbench()
    if request.task_type == "spi_master":
        return _spi_master_testbench()
    if request.task_type == "pwm_controller":
        return _pwm_controller_testbench(request.width)
    if request.task_type == "fir_filter":
        return _fir_filter_testbench(request.width)
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_testbench(request.width)
    if request.task_type == "matrix_vector_mac":
        return _matrix_vector_mac_testbench(request.width)
    if request.task_type == "composed_event_counter":
        return _composed_event_counter_testbench(request.width)
    if request.task_type == "composed_stream_accumulator":
        return _composed_stream_accumulator_testbench(request.width)
    if request.task_type == "composed_stream_fork":
        return _composed_stream_fork_testbench(request.width)
    if request.task_type == "composed_dual_stream_join":
        return _composed_dual_stream_join_testbench(request.width)
    if request.task_type == "composed_vector_mac_pipeline":
        return _composed_vector_mac_pipeline_testbench(request.width)
    if request.task_type == "composed_td_update_core":
        return _composed_td_update_core_testbench(request.width)
    if request.task_type == "composed_policy_value_shell":
        return _composed_policy_value_shell_testbench(request.width)
    if request.task_type == "composed_replay_sample_shell":
        return _composed_replay_sample_shell_testbench(request.width)
    if request.task_type == "composed_host_protocol_shell":
        return _composed_host_protocol_shell_testbench(request.width)
    if request.task_type == "composed_rl_accelerator_shell":
        return _composed_rl_accelerator_shell_testbench(request.width)
    if request.task_type == "composed_batch_rl_accelerator_shell":
        return _composed_batch_rl_accelerator_shell_testbench(request.width)
    if request.task_type == "composed_replay_arbiter_shell":
        return _composed_replay_arbiter_shell_testbench(request.width)
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")


def _counter_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg en;
          wire [{msb}:0] count;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .en(en),
            .count(count)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            en = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            en = 1'b1;
            repeat (4) @(posedge clk);
            if (count !== {width}'d4) begin
              $display("TEST_FAIL expected count=4 got %0d", count);
              $finish;
            end
            en = 1'b0;
            repeat (2) @(posedge clk);
            if (count !== {width}'d4) begin
              $display("TEST_FAIL hold failed got %0d", count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _fifo_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire wr_en,
            input wire rd_en,
            input wire [{msb}:0] din,
            output reg [{msb}:0] dout,
            output wire full,
            output wire empty
        );

          reg [{msb}:0] mem [0:3];
          reg [1:0] wr_ptr;
          reg [1:0] rd_ptr;
          reg [2:0] count;

          assign full = (count == 3'd4);
          assign empty = (count == 3'd0);

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              wr_ptr <= 2'd0;
              rd_ptr <= 2'd0;
              count <= 3'd0;
              dout <= {width}'d0;
            end else begin
              if (wr_en && !full) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 2'd1;
              end
              if (rd_en && !empty) begin
                dout <= mem[rd_ptr];
                rd_ptr <= rd_ptr + 2'd1;
              end
              case ({{wr_en && !full, rd_en && !empty}})
                2'b10: count <= count + 3'd1;
                2'b01: count <= count - 3'd1;
                default: count <= count;
              endcase
            end
          end

        endmodule
        """
    )


def _fifo_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg wr_en;
          reg rd_en;
          reg [{msb}:0] din;
          wire [{msb}:0] dout;
          wire full;
          wire empty;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .wr_en(wr_en),
            .rd_en(rd_en),
            .din(din),
            .dout(dout),
            .full(full),
            .empty(empty)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            wr_en = 1'b0;
            rd_en = 1'b0;
            din = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            din = {width}'d42;
            wr_en = 1'b1;
            @(negedge clk);
            wr_en = 1'b0;
            if (empty !== 1'b0) begin
              $display("TEST_FAIL fifo should not be empty after write");
              $finish;
            end

            rd_en = 1'b1;
            @(negedge clk);
            rd_en = 1'b0;
            @(negedge clk);
            if (dout !== {width}'d42) begin
              $display("TEST_FAIL expected dout=42 got %0d", dout);
              $finish;
            end
            if (empty !== 1'b1) begin
              $display("TEST_FAIL fifo should be empty after read");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _simple_fsm_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            output reg done,
            output reg [{msb}:0] state_value
        );

          localparam [1:0] IDLE = 2'd0;
          localparam [1:0] RUN = 2'd1;
          localparam [1:0] DONE = 2'd2;

          reg [1:0] state;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              state <= IDLE;
              done <= 1'b0;
              state_value <= {width}'d0;
            end else begin
              case (state)
                IDLE: begin
                  done <= 1'b0;
                  state_value <= {width}'d0;
                  if (start) begin
                    state <= RUN;
                  end
                end
                RUN: begin
                  state_value <= state_value + {{ {width - 1}'d0, 1'b1 }};
                  if (state_value == {width}'d2) begin
                    state <= DONE;
                  end
                end
                DONE: begin
                  done <= 1'b1;
                  if (!start) begin
                    state <= IDLE;
                  end
                end
                default: begin
                  state <= IDLE;
                end
              endcase
            end
          end

        endmodule
        """
    )


def _simple_fsm_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          wire done;
          wire [{msb}:0] state_value;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .done(done),
            .state_value(state_value)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            @(negedge clk);
            start = 1'b1;
            repeat (5) @(posedge clk);
            if (done !== 1'b1) begin
              $display("TEST_FAIL fsm did not reach done");
              $finish;
            end
            @(negedge clk);
            start = 1'b0;
            repeat (2) @(posedge clk);
            if (done !== 1'b0) begin
              $display("TEST_FAIL fsm did not return to idle");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _ram_read_write_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire we,
            input wire [1:0] addr,
            input wire [{msb}:0] wdata,
            output reg [{msb}:0] rdata
        );

          reg [{msb}:0] mem [0:3];
          integer i;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              rdata <= {width}'d0;
              for (i = 0; i < 4; i = i + 1) begin
                mem[i] <= {width}'d0;
              end
            end else begin
              if (we) begin
                mem[addr] <= wdata;
              end
              rdata <= mem[addr];
            end
          end

        endmodule
        """
    )


def _ram_read_write_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg we;
          reg [1:0] addr;
          reg [{msb}:0] wdata;
          wire [{msb}:0] rdata;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .we(we),
            .addr(addr),
            .wdata(wdata),
            .rdata(rdata)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            we = 1'b0;
            addr = 2'd0;
            wdata = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            addr = 2'd2;
            wdata = {width}'d99;
            we = 1'b1;
            @(negedge clk);
            we = 1'b0;
            @(negedge clk);
            if (rdata !== {width}'d99) begin
              $display("TEST_FAIL expected rdata=99 got %0d", rdata);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _passthrough_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg [{msb}:0] din;
          wire [{msb}:0] dout;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .din(din),
            .dout(dout)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            din = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            din = {width}'d165;
            #1;
            if (dout !== {width}'d165) begin
              $display("TEST_FAIL expected dout=165 got %0d", dout);
              $finish;
            end

            @(negedge clk);
            din = {width}'d90;
            #1;
            if (dout !== {width}'d90) begin
              $display("TEST_FAIL expected dout=90 got %0d", dout);
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _uart_tx_testbench() -> str:
    return dedent(
        """\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          reg [7:0] data;
          wire tx;
          wire busy;
          wire done;
          reg [7:0] expected_bits;
          integer i;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .data(data),
            .tx(tx),
            .busy(busy),
            .done(done)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            data = 8'd0;
            expected_bits = 8'hA5;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            data = 8'hA5;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            #1;
            if (tx !== 1'b0) begin
              $display("TEST_FAIL start bit expected 0 got %0b", tx);
              $finish;
            end
            if (busy !== 1'b1) begin
              $display("TEST_FAIL busy was not asserted");
              $finish;
            end

            for (i = 0; i < 8; i = i + 1) begin
              repeat (4) @(posedge clk);
              #1;
              if (tx !== expected_bits[i]) begin
                $display(
                  "TEST_FAIL data bit %0d expected %0b got %0b",
                  i,
                  expected_bits[i],
                  tx
                );
                $finish;
              end
            end

            repeat (4) @(posedge clk);
            #1;
            if (tx !== 1'b1) begin
              $display("TEST_FAIL stop bit expected 1 got %0b", tx);
              $finish;
            end

            repeat (4) @(posedge clk);
            #1;
            if (done !== 1'b1) begin
              $display("TEST_FAIL done was not asserted");
              $finish;
            end
            if (busy !== 1'b0) begin
              $display("TEST_FAIL busy did not clear");
              $finish;
            end
            @(posedge clk);
            #1;
            if (done !== 1'b0) begin
              $display("TEST_FAIL done was not one cycle");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _spi_master_testbench() -> str:
    return dedent(
        """\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          reg [7:0] tx_data;
          reg miso;
          wire [7:0] rx_data;
          wire busy;
          wire done;
          wire sclk;
          wire mosi;
          wire cs_n;

          reg [7:0] miso_pattern;
          integer miso_bit;
          integer sclk_edge_count;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .tx_data(tx_data),
            .miso(miso),
            .rx_data(rx_data),
            .busy(busy),
            .done(done),
            .sclk(sclk),
            .mosi(mosi),
            .cs_n(cs_n)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          always @(negedge sclk or posedge cs_n) begin
            if (cs_n) begin
              miso_bit = 7;
              miso = miso_pattern[7];
            end else if (miso_bit > 0) begin
              miso_bit = miso_bit - 1;
              miso = miso_pattern[miso_bit];
            end
          end

          always @(posedge sclk) begin
            if (!cs_n) begin
              sclk_edge_count = sclk_edge_count + 1;
            end
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            tx_data = 8'd0;
            miso_pattern = 8'h3C;
            miso_bit = 7;
            sclk_edge_count = 0;
            miso = miso_pattern[7];
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            tx_data = 8'hA5;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            #1;
            if (busy !== 1'b1 || cs_n !== 1'b0) begin
              $display("TEST_FAIL transfer did not start");
              $finish;
            end
            if (mosi !== 1'b1) begin
              $display("TEST_FAIL expected first MOSI bit 1 got %0b", mosi);
              $finish;
            end

            while (done !== 1'b1) begin
              @(posedge clk);
            end
            #1;
            if (cs_n !== 1'b1) begin
              $display("TEST_FAIL cs_n was not released");
              $finish;
            end
            if (sclk_edge_count != 8) begin
              $display("TEST_FAIL expected 8 SCLK rising edges got %0d", sclk_edge_count);
              $finish;
            end
            if (rx_data !== 8'h3C) begin
              $display("TEST_FAIL expected rx_data=3c got %02h", rx_data);
              $finish;
            end
            @(posedge clk);
            #1;
            if (done !== 1'b0) begin
              $display("TEST_FAIL done was not one cycle");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _pwm_controller_testbench(width: int) -> str:
    msb = width - 1
    duty_value = 3 if width >= 3 else max(1, (1 << width) - 1)
    sample_cycles = 8 if width >= 3 else 1 << width
    expected_high = 3 if width >= 3 else duty_value
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg [{msb}:0] duty;
          wire pwm_out;
          integer high_count;
          integer i;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .duty(duty),
            .pwm_out(pwm_out)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            duty = {width}'d{duty_value};
            repeat (2) @(posedge clk);
            @(negedge clk);
            rst_n = 1'b1;

            high_count = 0;
            #1;
            if (pwm_out === 1'b1) begin
              high_count = high_count + 1;
            end
            for (i = 1; i < {sample_cycles}; i = i + 1) begin
              @(posedge clk);
              #1;
              if (pwm_out === 1'b1) begin
                high_count = high_count + 1;
              end
            end

            if (high_count != {expected_high}) begin
              $display("TEST_FAIL expected %0d high cycles got %0d", {expected_high}, high_count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _streaming_valid_ready_testbench(width: int) -> str:
    msb = width - 1
    mask = (1 << width) - 1
    first_value = 0x12 & mask
    second_value = 0xA5 & mask
    if first_value == second_value:
        second_value = (~first_value) & mask
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          wire out_valid;
          reg out_ready;
          wire [{msb}:0] out_data;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_word;
            input [{msb}:0] value;
            begin
              @(negedge clk);
              in_data = value;
              in_valid = 1'b1;
              while (in_ready !== 1'b1) begin
                @(negedge clk);
              end
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task expect_word;
            input [{msb}:0] value;
            begin
              while (out_valid !== 1'b1) begin
                @(posedge clk);
              end
              #1;
              if (out_data !== value) begin
                $display("TEST_FAIL expected output %0d got %0d", value, out_data);
                $finish;
              end
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_word({width}'d{first_value});
            expect_word({width}'d{first_value});
            @(posedge clk);
            #1;

            out_ready = 1'b0;
            send_word({width}'d{second_value});
            repeat (2) @(posedge clk);
            #1;
            if (out_valid !== 1'b1) begin
              $display("TEST_FAIL stalled output was not held valid");
              $finish;
            end
            out_ready = 1'b1;
            expect_word({width}'d{second_value});
            @(posedge clk);
            #1;

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _fir_filter_testbench(width: int) -> str:
    msb = width - 1
    result_msb = width + 2
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg sample_valid;
          reg [{msb}:0] sample;
          wire result_valid;
          wire [{result_msb}:0] result;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample(sample),
            .result_valid(result_valid),
            .result(result)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_and_expect;
            input [{msb}:0] value;
            input [{result_msb}:0] expected;
            begin
              @(negedge clk);
              sample = value;
              sample_valid = 1'b1;
              @(posedge clk);
              #1;
              if (result_valid !== 1'b1) begin
                $display("TEST_FAIL result_valid was not asserted");
                $finish;
              end
              if (result !== expected) begin
                $display("TEST_FAIL expected result=%0d got %0d", expected, result);
                $finish;
              end
              @(negedge clk);
              sample_valid = 1'b0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            sample_valid = 1'b0;
            sample = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_and_expect({width}'d1, {width + 3}'d1);
            send_and_expect({width}'d2, {width + 3}'d4);
            send_and_expect({width}'d3, {width + 3}'d8);

            @(posedge clk);
            #1;
            if (result_valid !== 1'b0) begin
              $display("TEST_FAIL result_valid did not clear");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _matrix_vector_mac_testbench(width: int) -> str:
    result_msb = width + 3
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          wire busy;
          wire done;
          wire [{result_msb}:0] result;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .busy(busy),
            .done(done),
            .result(result)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            while (done !== 1'b1) begin
              @(posedge clk);
            end
            #1;
            if (busy !== 1'b0) begin
              $display("TEST_FAIL busy did not clear");
              $finish;
            end
            if (result !== {width + 4}'d17) begin
              $display("TEST_FAIL expected result=17 got %0d", result);
              $finish;
            end
            @(posedge clk);
            #1;
            if (done !== 1'b0) begin
              $display("TEST_FAIL done was not one cycle");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_stream_accumulator_testbench(width: int) -> str:
    msb = width - 1
    sum_msb = width + 3
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          wire sample_valid;
          wire [{sum_msb}:0] sum;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .sample_valid(sample_valid),
            .sum(sum)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_sample;
            input [{msb}:0] value;
            begin
              @(negedge clk);
              in_valid = 1'b1;
              in_data = value;
              @(negedge clk);
              in_valid = 1'b0;
              in_data = {width}'d0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_sample({width}'d3);
            send_sample({width}'d4);
            repeat (2) @(posedge clk);
            #1;

            if (sum !== {width + 4}'d7) begin
              $display("TEST_FAIL expected sum=7 got %0d", sum);
              $finish;
            end
            if (in_ready !== 1'b1) begin
              $display("TEST_FAIL in_ready not asserted");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_event_counter_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg event_valid;
          wire [{msb}:0] count;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .event_valid(event_valid),
            .count(count)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task pulse_event;
            begin
              @(negedge clk);
              event_valid = 1'b1;
              @(negedge clk);
              event_valid = 1'b0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            event_valid = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            pulse_event();
            pulse_event();
            repeat (2) @(posedge clk);
            #1;
            if (count !== {width}'d2) begin
              $display("TEST_FAIL expected count=2 got %0d", count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_stream_fork_testbench(width: int) -> str:
    msb = width - 1
    first_value = min(0xA5, (1 << width) - 1)
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          wire out0_valid;
          reg out0_ready;
          wire [{msb}:0] out0_data;
          wire out1_valid;
          reg out1_ready;
          wire [{msb}:0] out1_data;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out0_valid(out0_valid),
            .out0_ready(out0_ready),
            .out0_data(out0_data),
            .out1_valid(out1_valid),
            .out1_ready(out1_ready),
            .out1_data(out1_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            out0_ready = 1'b1;
            out1_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            in_valid = 1'b1;
            in_data = {width}'d{first_value};
            @(negedge clk);
            in_valid = 1'b0;
            in_data = {width}'d0;
            repeat (3) @(posedge clk);
            #1;

            if (out0_valid !== 1'b1 || out1_valid !== 1'b1) begin
              $display("TEST_FAIL fork outputs not valid");
              $finish;
            end
            if (out0_data !== {width}'d{first_value} || out1_data !== {width}'d{first_value}) begin
              $display("TEST_FAIL fork data mismatch out0=%0d out1=%0d", out0_data, out1_data);
              $finish;
            end
            if (in_ready !== 1'b1) begin
              $display("TEST_FAIL fork input not ready");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_dual_stream_join_testbench(width: int) -> str:
    msb = width - 1
    sum_width = width + 4
    sum_msb = sum_width - 1
    expected_pair_sum = 8
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in0_valid;
          wire in0_ready;
          reg [{msb}:0] in0_data;
          reg in1_valid;
          wire in1_ready;
          reg [{msb}:0] in1_data;
          wire out_valid;
          reg out_ready;
          wire [{sum_msb}:0] out_data;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in0_valid(in0_valid),
            .in0_ready(in0_ready),
            .in0_data(in0_data),
            .in1_valid(in1_valid),
            .in1_ready(in1_ready),
            .in1_data(in1_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            in0_valid = 1'b0;
            in0_data = {width}'d0;
            in1_valid = 1'b0;
            in1_data = {width}'d0;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            in0_valid = 1'b1;
            in0_data = {width}'d3;
            in1_valid = 1'b1;
            in1_data = {width}'d5;
            @(negedge clk);
            in0_valid = 1'b0;
            in1_valid = 1'b0;
            in0_data = {width}'d0;
            in1_data = {width}'d0;
            wait_cycles = 0;
            while (out_valid !== 1'b1 && wait_cycles < 8) begin
              @(posedge clk);
              #1;
              wait_cycles = wait_cycles + 1;
            end
            #1;

            if (out_valid !== 1'b1) begin
              $display("TEST_FAIL joined output not valid");
              $finish;
            end
            if (out_data !== {sum_width}'d{expected_pair_sum}) begin
              $display("TEST_FAIL expected joined sum=%0d got %0d", {expected_pair_sum}, out_data);
              $finish;
            end
            if (in0_ready !== 1'b1 || in1_ready !== 1'b1) begin
              $display("TEST_FAIL joined inputs not ready");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_vector_mac_pipeline_testbench(width: int) -> str:
    msb = width - 1
    score_width = width * 2
    score_msb = score_width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg feature_valid;
          wire feature_ready;
          reg [{msb}:0] feature_data;
          reg weight_valid;
          wire weight_ready;
          reg [{msb}:0] weight_data;
          reg [{score_msb}:0] bias;
          wire score_valid;
          reg score_ready;
          wire [{score_msb}:0] score_data;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .feature_valid(feature_valid),
            .feature_ready(feature_ready),
            .feature_data(feature_data),
            .weight_valid(weight_valid),
            .weight_ready(weight_ready),
            .weight_data(weight_data),
            .bias(bias),
            .score_valid(score_valid),
            .score_ready(score_ready),
            .score_data(score_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_pair;
            input [{msb}:0] feature;
            input [{msb}:0] weight;
            begin
              @(negedge clk);
              feature_valid = 1'b1;
              weight_valid = 1'b1;
              feature_data = feature;
              weight_data = weight;
              while (!(feature_ready && weight_ready)) begin
                @(negedge clk);
              end
              @(negedge clk);
              feature_valid = 1'b0;
              weight_valid = 1'b0;
              feature_data = {width}'d0;
              weight_data = {width}'d0;
            end
          endtask

          task expect_score;
            input [{score_msb}:0] expected;
            begin
              wait_cycles = 0;
              while (score_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (score_valid !== 1'b1) begin
                $display("TEST_FAIL score did not become valid");
                $finish;
              end
              if (score_data !== expected) begin
                $display("TEST_FAIL expected score=%0d got %0d", expected, score_data);
                $finish;
              end
              @(negedge clk);
            end
          endtask

          initial begin
            rst_n = 1'b0;
            feature_valid = 1'b0;
            feature_data = {width}'d0;
            weight_valid = 1'b0;
            weight_data = {width}'d0;
            bias = {score_width}'d0;
            score_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            bias = {score_width}'d3;
            send_pair({width}'d1, {width}'d2);
            send_pair({width}'d2, {width}'d3);
            send_pair({width}'d3, {width}'d4);
            send_pair({width}'d4, {width}'d5);
            expect_score({score_width}'d43);

            bias = {score_width}'d1;
            send_pair({width}'d2, {width}'d1);
            send_pair({width}'d1, {width}'d2);
            send_pair({width}'d0, {width}'d3);
            send_pair({width}'d3, {width}'d4);
            expect_score({score_width}'d17);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_td_update_core_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg signed [{msb}:0] reward;
          reg signed [{msb}:0] value;
          reg signed [{msb}:0] next_value;
          reg [{msb}:0] gamma;
          reg [{msb}:0] alpha;
          wire out_valid;
          reg out_ready;
          wire signed [{msb}:0] td_error;
          wire signed [{msb}:0] updated_value;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .reward(reward),
            .value(value),
            .next_value(next_value),
            .gamma(gamma),
            .alpha(alpha),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .td_error(td_error),
            .updated_value(updated_value)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_update;
            input signed [{msb}:0] reward_i;
            input signed [{msb}:0] value_i;
            input signed [{msb}:0] next_value_i;
            input [{msb}:0] gamma_i;
            input [{msb}:0] alpha_i;
            begin
              @(negedge clk);
              in_valid = 1'b1;
              reward = reward_i;
              value = value_i;
              next_value = next_value_i;
              gamma = gamma_i;
              alpha = alpha_i;
              while (!in_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task expect_update;
            input signed [{msb}:0] expected_error;
            input signed [{msb}:0] expected_value;
            begin
              wait_cycles = 0;
              while (out_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (out_valid !== 1'b1) begin
                $display("TEST_FAIL output did not become valid");
                $finish;
              end
              if (td_error !== expected_error || updated_value !== expected_value) begin
                $display(
                  "TEST_FAIL expected td=%0d value=%0d got td=%0d value=%0d",
                  expected_error,
                  expected_value,
                  td_error,
                  updated_value
                );
                $finish;
              end
              @(negedge clk);
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            reward = {width}'sd0;
            value = {width}'sd0;
            next_value = {width}'sd0;
            gamma = {width}'d0;
            alpha = {width}'d0;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_update({width}'sd4, {width}'sd10, {width}'sd20, {width}'d8, {width}'d4);
            expect_update({width}'sd4, {width}'sd11);

            send_update({width}'sd2, {width}'sd6, {width}'sd16, {width}'d8, {width}'d8);
            expect_update({width}'sd4, {width}'sd8);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_policy_value_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg cfg_valid;
          wire cfg_ready;
          reg [2:0] cfg_addr;
          reg [{msb}:0] cfg_data;
          reg obs_valid;
          wire obs_ready;
          reg [{msb}:0] obs0;
          reg [{msb}:0] obs1;
          wire action_valid;
          reg action_ready;
          wire selected_action;
          wire [{msb}:0] value_estimate;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .obs_valid(obs_valid),
            .obs_ready(obs_ready),
            .obs0(obs0),
            .obs1(obs1),
            .action_valid(action_valid),
            .action_ready(action_ready),
            .selected_action(selected_action),
            .value_estimate(value_estimate)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_cfg;
            input [2:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              cfg_valid = 1'b1;
              cfg_addr = addr_i;
              cfg_data = data_i;
              while (!cfg_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              cfg_valid = 1'b0;
            end
          endtask

          task send_observation;
            input [{msb}:0] obs0_i;
            input [{msb}:0] obs1_i;
            begin
              @(negedge clk);
              obs_valid = 1'b1;
              obs0 = obs0_i;
              obs1 = obs1_i;
              while (!obs_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              obs_valid = 1'b0;
            end
          endtask

          task expect_action;
            input expected_action;
            input [{msb}:0] expected_value;
            begin
              wait_cycles = 0;
              while (action_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (action_valid !== 1'b1) begin
                $display("TEST_FAIL action output did not become valid");
                $finish;
              end
              if (selected_action !== expected_action || value_estimate !== expected_value) begin
                $display(
                  "TEST_FAIL expected action=%0d value=%0d got action=%0d value=%0d",
                  expected_action,
                  expected_value,
                  selected_action,
                  value_estimate
                );
                $finish;
              end
              @(negedge clk);
            end
          endtask

          initial begin
            rst_n = 1'b0;
            cfg_valid = 1'b0;
            cfg_addr = 3'd0;
            cfg_data = {width}'d0;
            obs_valid = 1'b0;
            obs0 = {width}'d0;
            obs1 = {width}'d0;
            action_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_cfg(3'd0, {width}'d2);
            write_cfg(3'd1, {width}'d1);
            write_cfg(3'd2, {width}'d3);
            write_cfg(3'd3, {width}'d0);
            write_cfg(3'd4, {width}'d1);

            send_observation({width}'d4, {width}'d2);
            expect_action(1'b0, {width}'d7);

            send_observation({width}'d1, {width}'d5);
            expect_action(1'b1, {width}'d9);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_replay_sample_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg host_valid;
          wire host_ready;
          reg [{msb}:0] host_state;
          reg host_action;
          reg [{msb}:0] host_reward;
          reg [{msb}:0] host_next_state;
          reg host_done;
          wire sample_valid;
          reg sample_ready;
          wire [{msb}:0] sample_state;
          wire sample_action;
          wire [{msb}:0] sample_reward;
          wire [{msb}:0] sample_next_state;
          wire sample_done;
          wire [2:0] occupancy;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .host_valid(host_valid),
            .host_ready(host_ready),
            .host_state(host_state),
            .host_action(host_action),
            .host_reward(host_reward),
            .host_next_state(host_next_state),
            .host_done(host_done),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample_state(sample_state),
            .sample_action(sample_action),
            .sample_reward(sample_reward),
            .sample_next_state(sample_next_state),
            .sample_done(sample_done),
            .occupancy(occupancy)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_sample;
            input [{msb}:0] state_i;
            input action_i;
            input [{msb}:0] reward_i;
            input [{msb}:0] next_state_i;
            input done_i;
            begin
              @(negedge clk);
              host_valid = 1'b1;
              host_state = state_i;
              host_action = action_i;
              host_reward = reward_i;
              host_next_state = next_state_i;
              host_done = done_i;
              while (!host_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              host_valid = 1'b0;
            end
          endtask

          task expect_sample;
            input [{msb}:0] expected_state;
            input expected_action;
            input [{msb}:0] expected_reward;
            input [{msb}:0] expected_next_state;
            input expected_done;
            begin
              wait_cycles = 0;
              while (sample_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (sample_valid !== 1'b1) begin
                $display("TEST_FAIL sample output did not become valid");
                $finish;
              end
              if (
                sample_state !== expected_state ||
                sample_action !== expected_action ||
                sample_reward !== expected_reward ||
                sample_next_state !== expected_next_state ||
                sample_done !== expected_done
              ) begin
                $display(
                  "TEST_FAIL expected s=%0d a=%0d r=%0d ns=%0d d=%0d got s=%0d a=%0d r=%0d ns=%0d d=%0d",
                  expected_state,
                  expected_action,
                  expected_reward,
                  expected_next_state,
                  expected_done,
                  sample_state,
                  sample_action,
                  sample_reward,
                  sample_next_state,
                  sample_done
                );
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            host_valid = 1'b0;
            host_state = {width}'d0;
            host_action = 1'b0;
            host_reward = {width}'d0;
            host_next_state = {width}'d0;
            host_done = 1'b0;
            sample_ready = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_sample({width}'d3, 1'b1, {width}'d4, {width}'d5, 1'b0);
            write_sample({width}'d8, 1'b0, {width}'d2, {width}'d9, 1'b1);
            write_sample({width}'d1, 1'b1, {width}'d7, {width}'d6, 1'b0);
            @(posedge clk);
            #1;
            if (occupancy !== 3'd3) begin
              $display("TEST_FAIL expected occupancy 3 got %0d", occupancy);
              $finish;
            end

            sample_ready = 1'b1;
            expect_sample({width}'d3, 1'b1, {width}'d4, {width}'d5, 1'b0);
            expect_sample({width}'d8, 1'b0, {width}'d2, {width}'d9, 1'b1);
            expect_sample({width}'d1, 1'b1, {width}'d7, {width}'d6, 1'b0);
            @(posedge clk);
            #1;
            if (occupancy !== 3'd0) begin
              $display("TEST_FAIL expected occupancy 0 got %0d", occupancy);
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_host_protocol_shell_testbench(width: int) -> str:
    msb = width - 1
    stream_msb = width * 2 - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg s_axi_awvalid;
          wire s_axi_awready;
          reg [3:0] s_axi_awaddr;
          reg s_axi_wvalid;
          wire s_axi_wready;
          reg [{msb}:0] s_axi_wdata;
          reg s_axi_wstrb;
          wire s_axi_bvalid;
          reg s_axi_bready;
          reg s_axi_arvalid;
          wire s_axi_arready;
          reg [3:0] s_axi_araddr;
          wire s_axi_rvalid;
          reg s_axi_rready;
          wire [{msb}:0] s_axi_rdata;
          wire m_axis_tvalid;
          reg m_axis_tready;
          wire [{stream_msb}:0] m_axis_tdata;
          wire m_axis_tlast;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .s_axi_awvalid(s_axi_awvalid),
            .s_axi_awready(s_axi_awready),
            .s_axi_awaddr(s_axi_awaddr),
            .s_axi_wvalid(s_axi_wvalid),
            .s_axi_wready(s_axi_wready),
            .s_axi_wdata(s_axi_wdata),
            .s_axi_wstrb(s_axi_wstrb),
            .s_axi_bvalid(s_axi_bvalid),
            .s_axi_bready(s_axi_bready),
            .s_axi_arvalid(s_axi_arvalid),
            .s_axi_arready(s_axi_arready),
            .s_axi_araddr(s_axi_araddr),
            .s_axi_rvalid(s_axi_rvalid),
            .s_axi_rready(s_axi_rready),
            .s_axi_rdata(s_axi_rdata),
            .m_axis_tvalid(m_axis_tvalid),
            .m_axis_tready(m_axis_tready),
            .m_axis_tdata(m_axis_tdata),
            .m_axis_tlast(m_axis_tlast),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task axi_write;
            input [3:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              s_axi_awvalid = 1'b1;
              s_axi_awaddr = addr_i;
              s_axi_wvalid = 1'b1;
              s_axi_wdata = data_i;
              s_axi_wstrb = 1'b1;
              s_axi_bready = 1'b1;
              while (!s_axi_awready || !s_axi_wready) begin
                @(negedge clk);
              end
              @(negedge clk);
              s_axi_awvalid = 1'b0;
              s_axi_wvalid = 1'b0;
              while (!s_axi_bvalid) begin
                @(negedge clk);
              end
              @(negedge clk);
              s_axi_bready = 1'b0;
            end
          endtask

          task axi_read_expect;
            input [3:0] addr_i;
            input [{msb}:0] mask_i;
            input [{msb}:0] expected_i;
            begin
              @(negedge clk);
              s_axi_arvalid = 1'b1;
              s_axi_araddr = addr_i;
              s_axi_rready = 1'b1;
              while (!s_axi_arready) begin
                @(negedge clk);
              end
              @(negedge clk);
              s_axi_arvalid = 1'b0;
              wait_cycles = 0;
              while (!s_axi_rvalid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!s_axi_rvalid) begin
                $display("TEST_FAIL read response did not become valid");
                $finish;
              end
              if ((s_axi_rdata & mask_i) !== expected_i) begin
                $display("TEST_FAIL expected read masked %0h got %0h", expected_i, s_axi_rdata & mask_i);
                $finish;
              end
              @(negedge clk);
              s_axi_rready = 1'b0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            s_axi_awvalid = 1'b0;
            s_axi_awaddr = 4'h0;
            s_axi_wvalid = 1'b0;
            s_axi_wdata = {width}'h00;
            s_axi_wstrb = 1'b0;
            s_axi_bready = 1'b0;
            s_axi_arvalid = 1'b0;
            s_axi_araddr = 4'h0;
            s_axi_rready = 1'b0;
            m_axis_tready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            axi_write(4'h4, {width}'h12);
            axi_write(4'h8, {width}'h34);
            axi_write(4'h0, {width}'h01);

            wait_cycles = 0;
            while (!m_axis_tvalid && wait_cycles < 16) begin
              @(posedge clk);
              #1;
              wait_cycles = wait_cycles + 1;
            end
            if (!m_axis_tvalid || m_axis_tdata !== {width * 2}'h3412 || m_axis_tlast !== 1'b1) begin
              $display("TEST_FAIL expected stream payload 0x3412 got valid=%0d data=%0h last=%0d",
                       m_axis_tvalid, m_axis_tdata, m_axis_tlast);
              $finish;
            end
            repeat (2) @(posedge clk);
            #1;
            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq set");
              $finish;
            end

            axi_read_expect(4'hc, {width}'h06, {width}'h06);
            axi_write(4'h0, {width}'h02);
            axi_read_expect(4'hc, {width}'h04, {width}'h00);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_rl_accelerator_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg cfg_valid;
          wire cfg_ready;
          reg [2:0] cfg_addr;
          reg [{msb}:0] cfg_data;
          reg sample_valid;
          wire sample_ready;
          reg [{msb}:0] obs0;
          reg [{msb}:0] obs1;
          reg [{msb}:0] reward;
          reg [{msb}:0] next_value;
          reg done_in;
          wire result_valid;
          reg result_ready;
          wire selected_action;
          wire [{msb}:0] value_estimate;
          wire [{msb}:0] updated_value;
          wire episode_done;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .obs0(obs0),
            .obs1(obs1),
            .reward(reward),
            .next_value(next_value),
            .done_in(done_in),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action(selected_action),
            .value_estimate(value_estimate),
            .updated_value(updated_value),
            .episode_done(episode_done),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_cfg;
            input [2:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              cfg_valid = 1'b1;
              cfg_addr = addr_i;
              cfg_data = data_i;
              while (!cfg_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              cfg_valid = 1'b0;
            end
          endtask

          task send_sample;
            input [{msb}:0] obs0_i;
            input [{msb}:0] obs1_i;
            input [{msb}:0] reward_i;
            input [{msb}:0] next_value_i;
            input done_i;
            begin
              @(negedge clk);
              sample_valid = 1'b1;
              obs0 = obs0_i;
              obs1 = obs1_i;
              reward = reward_i;
              next_value = next_value_i;
              done_in = done_i;
              while (!sample_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              sample_valid = 1'b0;
            end
          endtask

          task expect_result;
            input expected_action;
            input [{msb}:0] expected_value;
            input [{msb}:0] expected_updated;
            input expected_done;
            begin
              wait_cycles = 0;
              while (!result_valid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!result_valid) begin
                $display("TEST_FAIL result did not become valid");
                $finish;
              end
              if (selected_action !== expected_action ||
                  value_estimate !== expected_value ||
                  updated_value !== expected_updated ||
                  episode_done !== expected_done) begin
                $display("TEST_FAIL expected action=%0d value=%0d updated=%0d done=%0d got action=%0d value=%0d updated=%0d done=%0d",
                         expected_action, expected_value, expected_updated, expected_done,
                         selected_action, value_estimate, updated_value, episode_done);
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            cfg_valid = 1'b0;
            cfg_addr = 3'd0;
            cfg_data = {width}'d0;
            sample_valid = 1'b0;
            obs0 = {width}'d0;
            obs1 = {width}'d0;
            reward = {width}'d0;
            next_value = {width}'d0;
            done_in = 1'b0;
            result_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_cfg(3'd0, {width}'d2);
            write_cfg(3'd1, {width}'d1);
            write_cfg(3'd2, {width}'d3);
            write_cfg(3'd3, {width}'d0);
            write_cfg(3'd4, {width}'d4);
            write_cfg(3'd5, {width}'d1);

            send_sample({width}'d4, {width}'d2, {width}'d1, {width}'d8, 1'b0);
            expect_result(1'b0, 8'd7, 8'd7, 1'b0);

            send_sample({width}'d1, {width}'d5, {width}'d2, {width}'d15, 1'b1);
            expect_result(1'b1, 8'd9, 8'd11, 1'b1);

            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq after done result");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_batch_rl_accelerator_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg cfg_valid;
          wire cfg_ready;
          reg [2:0] cfg_addr;
          reg [{msb}:0] cfg_data;
          reg batch_valid;
          wire batch_ready;
          reg [{msb}:0] obs0_a;
          reg [{msb}:0] obs1_a;
          reg [{msb}:0] reward_a;
          reg [{msb}:0] next_value_a;
          reg done_a;
          reg [{msb}:0] obs0_b;
          reg [{msb}:0] obs1_b;
          reg [{msb}:0] reward_b;
          reg [{msb}:0] next_value_b;
          reg done_b;
          wire result_valid;
          reg result_ready;
          wire selected_action_a;
          wire [{msb}:0] value_estimate_a;
          wire [{msb}:0] updated_value_a;
          wire selected_action_b;
          wire [{msb}:0] value_estimate_b;
          wire [{msb}:0] updated_value_b;
          wire batch_done;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .batch_valid(batch_valid),
            .batch_ready(batch_ready),
            .obs0_a(obs0_a),
            .obs1_a(obs1_a),
            .reward_a(reward_a),
            .next_value_a(next_value_a),
            .done_a(done_a),
            .obs0_b(obs0_b),
            .obs1_b(obs1_b),
            .reward_b(reward_b),
            .next_value_b(next_value_b),
            .done_b(done_b),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action_a(selected_action_a),
            .value_estimate_a(value_estimate_a),
            .updated_value_a(updated_value_a),
            .selected_action_b(selected_action_b),
            .value_estimate_b(value_estimate_b),
            .updated_value_b(updated_value_b),
            .batch_done(batch_done),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_cfg;
            input [2:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              cfg_valid = 1'b1;
              cfg_addr = addr_i;
              cfg_data = data_i;
              while (!cfg_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              cfg_valid = 1'b0;
            end
          endtask

          task send_batch;
            begin
              @(negedge clk);
              batch_valid = 1'b1;
              obs0_a = {width}'d4;
              obs1_a = {width}'d2;
              reward_a = {width}'d1;
              next_value_a = {width}'d8;
              done_a = 1'b0;
              obs0_b = {width}'d1;
              obs1_b = {width}'d5;
              reward_b = {width}'d2;
              next_value_b = {width}'d15;
              done_b = 1'b1;
              while (!batch_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              batch_valid = 1'b0;
            end
          endtask

          task expect_batch_result;
            input expected_action_a;
            input [{msb}:0] expected_value_a;
            input [{msb}:0] expected_updated_a;
            input expected_action_b;
            input [{msb}:0] expected_value_b;
            input [{msb}:0] expected_updated_b;
            input expected_batch_done;
            begin
              wait_cycles = 0;
              while (!result_valid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!result_valid) begin
                $display("TEST_FAIL batch result did not become valid");
                $finish;
              end
              if (selected_action_a !== expected_action_a ||
                  value_estimate_a !== expected_value_a ||
                  updated_value_a !== expected_updated_a ||
                  selected_action_b !== expected_action_b ||
                  value_estimate_b !== expected_value_b ||
                  updated_value_b !== expected_updated_b ||
                  batch_done !== expected_batch_done) begin
                $display("TEST_FAIL unexpected batch result");
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            cfg_valid = 1'b0;
            cfg_addr = 3'd0;
            cfg_data = {width}'d0;
            batch_valid = 1'b0;
            obs0_a = {width}'d0;
            obs1_a = {width}'d0;
            reward_a = {width}'d0;
            next_value_a = {width}'d0;
            done_a = 1'b0;
            obs0_b = {width}'d0;
            obs1_b = {width}'d0;
            reward_b = {width}'d0;
            next_value_b = {width}'d0;
            done_b = 1'b0;
            result_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_cfg(3'd0, {width}'d2);
            write_cfg(3'd1, {width}'d1);
            write_cfg(3'd2, {width}'d3);
            write_cfg(3'd3, {width}'d0);
            write_cfg(3'd4, {width}'d4);
            write_cfg(3'd5, {width}'d1);

            send_batch();
            expect_batch_result(1'b0, 8'd7, 8'd7, 1'b1, 8'd9, 8'd11, 1'b1);

            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq after batch done result");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _composed_replay_arbiter_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg host_valid;
          wire host_ready;
          reg [{msb}:0] host_state;
          reg host_action;
          reg [{msb}:0] host_reward;
          reg [{msb}:0] host_next_state;
          reg host_done;
          reg sample_req_valid;
          wire sample_req_ready;
          reg [1:0] sample_index;
          wire sample_valid;
          reg sample_ready;
          wire [{msb}:0] sample_state;
          wire sample_action;
          wire [{msb}:0] sample_reward;
          wire [{msb}:0] sample_next_state;
          wire sample_done;
          wire [2:0] occupancy;
          wire [1:0] write_index;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .host_valid(host_valid),
            .host_ready(host_ready),
            .host_state(host_state),
            .host_action(host_action),
            .host_reward(host_reward),
            .host_next_state(host_next_state),
            .host_done(host_done),
            .sample_req_valid(sample_req_valid),
            .sample_req_ready(sample_req_ready),
            .sample_index(sample_index),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample_state(sample_state),
            .sample_action(sample_action),
            .sample_reward(sample_reward),
            .sample_next_state(sample_next_state),
            .sample_done(sample_done),
            .occupancy(occupancy),
            .write_index(write_index),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_host_packet;
            input [{msb}:0] state_i;
            input action_i;
            input [{msb}:0] reward_i;
            input [{msb}:0] next_state_i;
            input done_i;
            begin
              @(negedge clk);
              host_valid = 1'b1;
              host_state = state_i;
              host_action = action_i;
              host_reward = reward_i;
              host_next_state = next_state_i;
              host_done = done_i;
              while (!host_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              host_valid = 1'b0;
            end
          endtask

          task request_sample;
            input [1:0] index_i;
            begin
              @(negedge clk);
              sample_req_valid = 1'b1;
              sample_index = index_i;
              while (!sample_req_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              sample_req_valid = 1'b0;
            end
          endtask

          task expect_sample;
            input [{msb}:0] expected_state;
            input expected_action;
            input [{msb}:0] expected_reward;
            input [{msb}:0] expected_next_state;
            input expected_done;
            begin
              wait_cycles = 0;
              while (!sample_valid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!sample_valid) begin
                $display("TEST_FAIL sample did not become valid");
                $finish;
              end
              if (sample_state !== expected_state ||
                  sample_action !== expected_action ||
                  sample_reward !== expected_reward ||
                  sample_next_state !== expected_next_state ||
                  sample_done !== expected_done) begin
                $display("TEST_FAIL unexpected sample packet");
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            host_valid = 1'b0;
            host_state = {width}'h00;
            host_action = 1'b0;
            host_reward = {width}'h00;
            host_next_state = {width}'h00;
            host_done = 1'b0;
            sample_req_valid = 1'b0;
            sample_index = 2'd0;
            sample_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_host_packet(8'h12, 1'b0, 8'h03, 8'h21, 1'b0);
            write_host_packet(8'h34, 1'b1, 8'h05, 8'h43, 1'b1);

            if (occupancy !== 3'd2 || write_index !== 2'd2) begin
              $display("TEST_FAIL expected occupancy=2 write_index=2");
              $finish;
            end

            request_sample(2'd0);
            expect_sample(8'h12, 1'b0, 8'h03, 8'h21, 1'b0);

            request_sample(2'd1);
            expect_sample(8'h34, 1'b1, 8'h05, 8'h43, 1'b1);

            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq after sample accepted");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _simple_passthrough_multimodule(task_name: str, width: int, submodule_name: str) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] din,
            output wire [{msb}:0] dout
        );

          {submodule_name} u_core (
            .clk(clk),
            .rst_n(rst_n),
            .din(din),
            .dout(dout)
          );

        endmodule
        """
    )
    core = dedent(
        f"""\
        module {submodule_name} (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] din,
            output wire [{msb}:0] dout
        );

          assign dout = rst_n ? din : {{{width}{{clk}}}};

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        f"rtl/{task_name}_core.v": core,
    }


def _uart_tx_rtl_files(width: int) -> dict[str, str]:
    top = dedent(
        """\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [7:0] data,
            output wire tx,
            output wire busy,
            output wire done
        );

          wire baud_tick;

          baud_tick_gen u_baud_tick_gen (
            .clk(clk),
            .rst_n(rst_n),
            .enable(busy),
            .tick(baud_tick)
          );

          uart_tx_core u_uart_tx_core (
            .clk(clk),
            .rst_n(rst_n),
            .baud_tick(baud_tick),
            .start(start),
            .data(data),
            .tx(tx),
            .busy(busy),
            .done(done)
          );

        endmodule
        """
    )
    baud_tick_gen = dedent(
        """\
        module baud_tick_gen (
            input wire clk,
            input wire rst_n,
            input wire enable,
            output wire tick
        );

          reg [1:0] div_count;

          assign tick = enable && (div_count == 2'd3);

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              div_count <= 2'd0;
            end else if (enable) begin
              div_count <= div_count + 2'd1;
            end else begin
              div_count <= 2'd0;
            end
          end

        endmodule
        """
    )
    uart_tx_core = dedent(
        """\
        module uart_tx_core (
            input wire clk,
            input wire rst_n,
            input wire baud_tick,
            input wire start,
            input wire [7:0] data,
            output reg tx,
            output reg busy,
            output reg done
        );

          localparam [1:0] IDLE = 2'd0;
          localparam [1:0] DATA = 2'd1;
          localparam [1:0] STOP = 2'd2;
          localparam [1:0] CLEANUP = 2'd3;

          reg [1:0] state;
          reg [2:0] bit_index;
          reg [7:0] shifter;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              state <= IDLE;
              bit_index <= 3'd0;
              shifter <= 8'd0;
              tx <= 1'b1;
              busy <= 1'b0;
              done <= 1'b0;
            end else begin
              done <= 1'b0;
              case (state)
                IDLE: begin
                  tx <= 1'b1;
                  busy <= 1'b0;
                  bit_index <= 3'd0;
                  if (start) begin
                    shifter <= data;
                    tx <= 1'b0;
                    busy <= 1'b1;
                    state <= DATA;
                  end
                end
                DATA: begin
                  if (baud_tick) begin
                    tx <= shifter[0];
                    shifter <= {1'b0, shifter[7:1]};
                    if (bit_index == 3'd7) begin
                      bit_index <= 3'd0;
                      state <= STOP;
                    end else begin
                      bit_index <= bit_index + 3'd1;
                    end
                  end
                end
                STOP: begin
                  if (baud_tick) begin
                    tx <= 1'b1;
                    state <= CLEANUP;
                  end
                end
                CLEANUP: begin
                  if (baud_tick) begin
                    tx <= 1'b1;
                    busy <= 1'b0;
                    done <= 1'b1;
                    state <= IDLE;
                  end
                end
                default: begin
                  state <= IDLE;
                  tx <= 1'b1;
                  busy <= 1'b0;
                end
              endcase
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/baud_tick_gen.v": baud_tick_gen,
        "rtl/uart_tx_core.v": uart_tx_core,
    }


def _spi_master_rtl_files(width: int) -> dict[str, str]:
    top = dedent(
        """\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [7:0] tx_data,
            input wire miso,
            output wire [7:0] rx_data,
            output wire busy,
            output wire done,
            output wire sclk,
            output wire mosi,
            output wire cs_n
        );

          wire spi_tick;

          clock_divider u_clock_divider (
            .clk(clk),
            .rst_n(rst_n),
            .enable(busy),
            .tick(spi_tick)
          );

          spi_master_core u_spi_master_core (
            .clk(clk),
            .rst_n(rst_n),
            .tick(spi_tick),
            .start(start),
            .tx_data(tx_data),
            .miso(miso),
            .rx_data(rx_data),
            .busy(busy),
            .done(done),
            .sclk(sclk),
            .mosi(mosi),
            .cs_n(cs_n)
          );

        endmodule
        """
    )
    clock_divider = dedent(
        """\
        module clock_divider (
            input wire clk,
            input wire rst_n,
            input wire enable,
            output wire tick
        );

          reg div_count;

          assign tick = enable && div_count;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              div_count <= 1'b0;
            end else if (enable) begin
              div_count <= ~div_count;
            end else begin
              div_count <= 1'b0;
            end
          end

        endmodule
        """
    )
    spi_master_core = dedent(
        """\
        module spi_master_core (
            input wire clk,
            input wire rst_n,
            input wire tick,
            input wire start,
            input wire [7:0] tx_data,
            input wire miso,
            output reg [7:0] rx_data,
            output reg busy,
            output reg done,
            output reg sclk,
            output reg mosi,
            output reg cs_n
        );

          reg [2:0] bit_index;
          reg [7:0] tx_shift;
          reg [6:0] rx_shift;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              bit_index <= 3'd0;
              tx_shift <= 8'd0;
              rx_shift <= 7'd0;
              rx_data <= 8'd0;
              busy <= 1'b0;
              done <= 1'b0;
              sclk <= 1'b0;
              mosi <= 1'b0;
              cs_n <= 1'b1;
            end else begin
              done <= 1'b0;
              if (!busy) begin
                sclk <= 1'b0;
                cs_n <= 1'b1;
                bit_index <= 3'd0;
                if (start) begin
                  busy <= 1'b1;
                  cs_n <= 1'b0;
                  tx_shift <= {tx_data[6:0], 1'b0};
                  rx_shift <= 7'd0;
                  mosi <= tx_data[7];
                end
              end else if (tick) begin
                if (sclk == 1'b0) begin
                  sclk <= 1'b1;
                  rx_shift <= {rx_shift[5:0], miso};
                  if (bit_index == 3'd7) begin
                    rx_data <= {rx_shift, miso};
                  end
                end else begin
                  sclk <= 1'b0;
                  if (bit_index == 3'd7) begin
                    busy <= 1'b0;
                    done <= 1'b1;
                    cs_n <= 1'b1;
                  end else begin
                    bit_index <= bit_index + 3'd1;
                    mosi <= tx_shift[7];
                    tx_shift <= {tx_shift[6:0], 1'b0};
                  end
                end
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/clock_divider.v": clock_divider,
        "rtl/spi_master_core.v": spi_master_core,
    }


def _pwm_controller_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] duty,
            output wire pwm_out
        );

          wire [{msb}:0] counter;

          pwm_timer #(
            .WIDTH({width})
          ) u_pwm_timer (
            .clk(clk),
            .rst_n(rst_n),
            .counter(counter)
          );

          pwm_channel #(
            .WIDTH({width})
          ) u_pwm_channel (
            .counter(counter),
            .duty(duty),
            .pwm_out(pwm_out)
          );

        endmodule
        """
    )
    pwm_timer = dedent(
        """\
        module pwm_timer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            output reg [WIDTH-1:0] counter
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              counter <= {WIDTH{1'b0}};
            end else begin
              counter <= counter + {{(WIDTH-1){1'b0}}, 1'b1};
            end
          end

        endmodule
        """
    )
    pwm_channel = dedent(
        """\
        module pwm_channel #(
            parameter WIDTH = 8
        ) (
            input wire [WIDTH-1:0] counter,
            input wire [WIDTH-1:0] duty,
            output wire pwm_out
        );

          assign pwm_out = (counter < duty);

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/pwm_timer.v": pwm_timer,
        "rtl/pwm_channel.v": pwm_channel,
    }


def _fir_filter_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    result_msb = width + 2
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            input wire [{msb}:0] sample,
            output wire result_valid,
            output wire [{result_msb}:0] result
        );

          // fir_filter_core contains the mac_unit tap helpers.
          fir_filter_core #(
            .WIDTH({width}),
            .RESULT_WIDTH({width + 3})
          ) u_fir_filter_core (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample(sample),
            .result_valid(result_valid),
            .result(result)
          );

        endmodule
        """
    )
    fir_filter_core = dedent(
        """\
        module fir_filter_core #(
            parameter WIDTH = 8,
            parameter RESULT_WIDTH = 11
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            input wire [WIDTH-1:0] sample,
            output reg result_valid,
            output reg [RESULT_WIDTH-1:0] result
        );

          reg [WIDTH-1:0] sample_d0;
          reg [WIDTH-1:0] sample_d1;
          wire [RESULT_WIDTH-1:0] stage0;
          wire [RESULT_WIDTH-1:0] stage1;
          wire [RESULT_WIDTH-1:0] filtered_result;

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_new_sample (
            .sample(sample),
            .coefficient(2'd1),
            .accum({RESULT_WIDTH{1'b0}}),
            .result(stage0)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_previous_sample (
            .sample(sample_d0),
            .coefficient(2'd2),
            .accum(stage0),
            .result(stage1)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_oldest_sample (
            .sample(sample_d1),
            .coefficient(2'd1),
            .accum(stage1),
            .result(filtered_result)
          );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sample_d0 <= {WIDTH{1'b0}};
              sample_d1 <= {WIDTH{1'b0}};
              result_valid <= 1'b0;
              result <= {RESULT_WIDTH{1'b0}};
            end else begin
              result_valid <= sample_valid;
              if (sample_valid) begin
                result <= filtered_result;
                sample_d1 <= sample_d0;
                sample_d0 <= sample;
              end
            end
          end

        endmodule
        """
    )
    mac_unit = dedent(
        """\
        module mac_unit #(
            parameter WIDTH = 8,
            parameter ACC_WIDTH = 11
        ) (
            input wire [WIDTH-1:0] sample,
            input wire [1:0] coefficient,
            input wire [ACC_WIDTH-1:0] accum,
            output wire [ACC_WIDTH-1:0] result
        );

          wire [ACC_WIDTH-1:0] extended_sample;
          wire [ACC_WIDTH-1:0] product_x1;
          wire [ACC_WIDTH-1:0] product_x2;

          assign extended_sample = {{(ACC_WIDTH-WIDTH){1'b0}}, sample};
          assign product_x1 = coefficient[0] ? extended_sample : {ACC_WIDTH{1'b0}};
          assign product_x2 = coefficient[1] ? (extended_sample << 1) : {ACC_WIDTH{1'b0}};
          assign result = accum + product_x1 + product_x2;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/fir_filter_core.v": fir_filter_core,
        "rtl/mac_unit.v": mac_unit,
    }


def _streaming_valid_ready_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [{msb}:0] out_data
        );

          wire skid_valid;
          wire skid_ready;
          wire [{msb}:0] skid_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(skid_valid),
            .out_ready(skid_ready),
            .out_data(skid_data)
          );

          stream_stage #(
            .WIDTH({width})
          ) u_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(skid_valid),
            .in_ready(skid_ready),
            .in_data(skid_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

        endmodule
        """
    )
    skid_buffer = dedent(
        """\
        module skid_buffer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          reg valid_r;
          reg [WIDTH-1:0] data_r;

          assign in_ready = !valid_r || out_ready;
          assign out_valid = valid_r;
          assign out_data = data_r;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_r <= 1'b0;
              data_r <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              valid_r <= in_valid;
              if (in_valid) begin
                data_r <= in_data;
              end
            end
          end

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output reg out_valid,
            input wire out_ready,
            output reg [WIDTH-1:0] out_data
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              out_data <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                out_data <= in_data;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/stream_stage.v": stream_stage,
    }


def _matrix_vector_mac_rtl_files(width: int) -> dict[str, str]:
    result_msb = width + 3
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            output wire busy,
            output wire done,
            output wire [{result_msb}:0] result
        );

          // dot_product_engine contains mac_unit and vector_rom instances.
          dot_product_engine #(
            .WIDTH({width}),
            .RESULT_WIDTH({width + 4})
          ) u_dot_product_engine (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .busy(busy),
            .done(done),
            .result(result)
          );

        endmodule
        """
    )
    dot_product_engine = dedent(
        """\
        module dot_product_engine #(
            parameter WIDTH = 8,
            parameter RESULT_WIDTH = 12
        ) (
            input wire clk,
            input wire rst_n,
            input wire start,
            output reg busy,
            output reg done,
            output reg [RESULT_WIDTH-1:0] result
        );

          reg [1:0] index;
          reg [RESULT_WIDTH-1:0] accum;
          reg [WIDTH-1:0] vector_value;
          wire [1:0] coefficient;
          wire [RESULT_WIDTH-1:0] next_accum;

          vector_rom u_vector_rom (
            .addr(index),
            .coefficient(coefficient)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_unit (
            .sample(vector_value),
            .coefficient(coefficient),
            .accum(accum),
            .result(next_accum)
          );

          always @* begin
            case (index)
              2'd0: vector_value = {{(WIDTH-1){1'b0}}, 1'b1};
              2'd1: vector_value = {{(WIDTH-2){1'b0}}, 2'd2};
              2'd2: vector_value = {{(WIDTH-2){1'b0}}, 2'd3};
              default: vector_value = {{(WIDTH-3){1'b0}}, 3'd4};
            endcase
          end

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              index <= 2'd0;
              accum <= {RESULT_WIDTH{1'b0}};
              busy <= 1'b0;
              done <= 1'b0;
              result <= {RESULT_WIDTH{1'b0}};
            end else begin
              done <= 1'b0;
              if (!busy) begin
                index <= 2'd0;
                accum <= {RESULT_WIDTH{1'b0}};
                if (start) begin
                  busy <= 1'b1;
                end
              end else begin
                accum <= next_accum;
                if (index == 2'd3) begin
                  result <= next_accum;
                  busy <= 1'b0;
                  done <= 1'b1;
                  index <= 2'd0;
                end else begin
                  index <= index + 2'd1;
                end
              end
            end
          end

        endmodule
        """
    )
    mac_unit = dedent(
        """\
        module mac_unit #(
            parameter WIDTH = 8,
            parameter ACC_WIDTH = 12
        ) (
            input wire [WIDTH-1:0] sample,
            input wire [1:0] coefficient,
            input wire [ACC_WIDTH-1:0] accum,
            output wire [ACC_WIDTH-1:0] result
        );

          wire [ACC_WIDTH-1:0] extended_sample;
          wire [ACC_WIDTH-1:0] product_x1;
          wire [ACC_WIDTH-1:0] product_x2;

          assign extended_sample = {{(ACC_WIDTH-WIDTH){1'b0}}, sample};
          assign product_x1 = coefficient[0] ? extended_sample : {ACC_WIDTH{1'b0}};
          assign product_x2 = coefficient[1] ? (extended_sample << 1) : {ACC_WIDTH{1'b0}};
          assign result = accum + product_x1 + product_x2;

        endmodule
        """
    )
    vector_rom = dedent(
        """\
        module vector_rom (
            input wire [1:0] addr,
            output reg [1:0] coefficient
        );

          always @* begin
            case (addr)
              2'd0: coefficient = 2'd2;
              2'd1: coefficient = 2'd1;
              2'd2: coefficient = 2'd3;
              default: coefficient = 2'd1;
            endcase
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/dot_product_engine.v": dot_product_engine,
        "rtl/mac_unit.v": mac_unit,
        "rtl/vector_rom.v": vector_rom,
    }


def _composed_stream_accumulator_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    sum_msb = width + 3
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            output wire sample_valid,
            output wire [{sum_msb}:0] sum
        );

          wire sample_ready;
          wire [{msb}:0] sample_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(sample_valid),
            .out_ready(sample_ready),
            .out_data(sample_data)
          );

          accumulator_core #(
            .WIDTH({width}),
            .SUM_WIDTH({width + 4})
          ) u_accumulator_core (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample(sample_data),
            .sum(sum)
          );

        endmodule
        """
    )
    skid_buffer = dedent(
        """\
        module skid_buffer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          reg valid_r;
          reg [WIDTH-1:0] data_r;

          assign in_ready = !valid_r || out_ready;
          assign out_valid = valid_r;
          assign out_data = data_r;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_r <= 1'b0;
              data_r <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              valid_r <= in_valid;
              if (in_valid) begin
                data_r <= in_data;
              end
            end
          end

        endmodule
        """
    )
    accumulator_core = dedent(
        """\
        module accumulator_core #(
            parameter WIDTH = 8,
            parameter SUM_WIDTH = 12
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            output wire sample_ready,
            input wire [WIDTH-1:0] sample,
            output reg [SUM_WIDTH-1:0] sum
        );

          assign sample_ready = 1'b1;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sum <= {SUM_WIDTH{1'b0}};
            end else if (sample_valid) begin
              sum <= sum + {{(SUM_WIDTH-WIDTH){1'b0}}, sample};
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/accumulator_core.v": accumulator_core,
    }


def _composed_event_counter_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire event_valid,
            output wire [{msb}:0] count
        );

          wire count_en;

          event_gate u_event_gate (
            .event_valid(event_valid),
            .count_en(count_en)
          );

          counter_core #(
            .WIDTH({width})
          ) u_counter_core (
            .clk(clk),
            .rst_n(rst_n),
            .en(count_en),
            .count(count)
          );

        endmodule
        """
    )
    event_gate = dedent(
        """\
        module event_gate (
            input wire event_valid,
            output wire count_en
        );

          assign count_en = event_valid;

        endmodule
        """
    )
    counter_core = dedent(
        """\
        module counter_core #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire en,
            output reg [WIDTH-1:0] count
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              count <= {WIDTH{1'b0}};
            end else if (en) begin
              count <= count + {{(WIDTH-1){1'b0}}, 1'b1};
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/event_gate.v": event_gate,
        "rtl/counter_core.v": counter_core,
    }


def _composed_stream_fork_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            output wire out0_valid,
            input wire out0_ready,
            output wire [{msb}:0] out0_data,
            output wire out1_valid,
            input wire out1_ready,
            output wire [{msb}:0] out1_data
        );

          wire fork_valid;
          wire fork_ready;
          wire [{msb}:0] fork_data;
          wire stage0_in_valid;
          wire stage0_in_ready;
          wire [{msb}:0] stage0_in_data;
          wire stage1_in_valid;
          wire stage1_in_ready;
          wire [{msb}:0] stage1_in_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(fork_valid),
            .out_ready(fork_ready),
            .out_data(fork_data)
          );

          stream_fork #(
            .WIDTH({width})
          ) u_stream_fork (
            .in_valid(fork_valid),
            .in_ready(fork_ready),
            .in_data(fork_data),
            .out0_valid(stage0_in_valid),
            .out0_ready(stage0_in_ready),
            .out0_data(stage0_in_data),
            .out1_valid(stage1_in_valid),
            .out1_ready(stage1_in_ready),
            .out1_data(stage1_in_data)
          );

          stream_stage #(
            .WIDTH({width})
          ) u_stage0 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(stage0_in_valid),
            .in_ready(stage0_in_ready),
            .in_data(stage0_in_data),
            .out_valid(out0_valid),
            .out_ready(out0_ready),
            .out_data(out0_data)
          );

          stream_stage #(
            .WIDTH({width})
          ) u_stage1 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(stage1_in_valid),
            .in_ready(stage1_in_ready),
            .in_data(stage1_in_data),
            .out_valid(out1_valid),
            .out_ready(out1_ready),
            .out_data(out1_data)
          );

        endmodule
        """
    )
    skid_buffer = dedent(
        """\
        module skid_buffer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          reg valid_r;
          reg [WIDTH-1:0] data_r;

          assign in_ready = !valid_r || out_ready;
          assign out_valid = valid_r;
          assign out_data = data_r;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_r <= 1'b0;
              data_r <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              valid_r <= in_valid;
              if (in_valid) begin
                data_r <= in_data;
              end
            end
          end

        endmodule
        """
    )
    stream_fork = dedent(
        """\
        module stream_fork #(
            parameter WIDTH = 8
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out0_valid,
            input wire out0_ready,
            output wire [WIDTH-1:0] out0_data,
            output wire out1_valid,
            input wire out1_ready,
            output wire [WIDTH-1:0] out1_data
        );

          assign in_ready = out0_ready && out1_ready;
          assign out0_valid = in_valid && out1_ready;
          assign out1_valid = in_valid && out0_ready;
          assign out0_data = in_data;
          assign out1_data = in_data;

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output reg out_valid,
            input wire out_ready,
            output reg [WIDTH-1:0] out_data
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              out_data <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                out_data <= in_data;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/stream_fork.v": stream_fork,
        "rtl/stream_stage.v": stream_stage,
    }


def _composed_dual_stream_join_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    sum_width = width + 4
    sum_msb = sum_width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in0_valid,
            output wire in0_ready,
            input wire [{msb}:0] in0_data,
            input wire in1_valid,
            output wire in1_ready,
            input wire [{msb}:0] in1_data,
            output wire out_valid,
            input wire out_ready,
            output wire [{sum_msb}:0] out_data
        );

          wire s0_valid;
          wire s0_ready;
          wire [{msb}:0] s0_data;
          wire s1_valid;
          wire s1_ready;
          wire [{msb}:0] s1_data;
          wire joined_valid;
          wire joined_ready;
          wire [{msb}:0] joined_data;
          wire accum_valid;
          wire accum_ready;
          wire [{sum_msb}:0] accum_sum;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid0 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in0_valid),
            .in_ready(in0_ready),
            .in_data(in0_data),
            .out_valid(s0_valid),
            .out_ready(s0_ready),
            .out_data(s0_data)
          );

          skid_buffer #(
            .WIDTH({width})
          ) u_skid1 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in1_valid),
            .in_ready(in1_ready),
            .in_data(in1_data),
            .out_valid(s1_valid),
            .out_ready(s1_ready),
            .out_data(s1_data)
          );

          stream_join #(
            .WIDTH({width})
          ) u_stream_join (
            .in0_valid(s0_valid),
            .in0_ready(s0_ready),
            .in0_data(s0_data),
            .in1_valid(s1_valid),
            .in1_ready(s1_ready),
            .in1_data(s1_data),
            .out_valid(joined_valid),
            .out_ready(joined_ready),
            .out_data(joined_data)
          );

          accumulator_core #(
            .WIDTH({width})
          ) u_accumulator_core (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(joined_valid),
            .sample_ready(joined_ready),
            .sample(joined_data),
            .sum(accum_sum)
          );

          assign accum_valid = joined_valid && joined_ready;

          stream_stage #(
            .WIDTH({sum_width})
          ) u_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(accum_valid),
            .in_ready(accum_ready),
            .in_data(accum_sum),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

        endmodule
        """
    )
    skid_buffer = dedent(
        """\
        module skid_buffer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          reg valid_r;
          reg [WIDTH-1:0] data_r;

          assign in_ready = !valid_r || out_ready;
          assign out_valid = valid_r;
          assign out_data = data_r;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_r <= 1'b0;
              data_r <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              valid_r <= in_valid;
              if (in_valid) begin
                data_r <= in_data;
              end
            end
          end

        endmodule
        """
    )
    stream_join = dedent(
        """\
        module stream_join #(
            parameter WIDTH = 8
        ) (
            input wire in0_valid,
            output wire in0_ready,
            input wire [WIDTH-1:0] in0_data,
            input wire in1_valid,
            output wire in1_ready,
            input wire [WIDTH-1:0] in1_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          assign out_valid = in0_valid && in1_valid;
          assign in0_ready = out_ready && in1_valid;
          assign in1_ready = out_ready && in0_valid;
          assign out_data = in0_data + in1_data;

        endmodule
        """
    )
    accumulator_core = dedent(
        """\
        module accumulator_core #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            output wire sample_ready,
            input wire [WIDTH-1:0] sample,
            output wire [WIDTH+3:0] sum
        );

          reg [WIDTH+3:0] sum_r;

          assign sample_ready = 1'b1;
          assign sum = sum_r + ((sample_valid && sample_ready) ? {{4{1'b0}}, sample} : {(WIDTH+4){1'b0}});

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sum_r <= {(WIDTH+4){1'b0}};
            end else if (sample_valid && sample_ready) begin
              sum_r <= sum;
            end
          end

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output reg out_valid,
            input wire out_ready,
            output reg [WIDTH-1:0] out_data
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              out_data <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                out_data <= in_data;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/stream_join.v": stream_join,
        "rtl/accumulator_core.v": accumulator_core,
        "rtl/stream_stage.v": stream_stage,
    }


def _composed_vector_mac_pipeline_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    score_width = width * 2
    score_msb = score_width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire feature_valid,
            output wire feature_ready,
            input wire [{msb}:0] feature_data,
            input wire weight_valid,
            output wire weight_ready,
            input wire [{msb}:0] weight_data,
            input wire [{score_msb}:0] bias,
            output wire score_valid,
            input wire score_ready,
            output wire [{score_msb}:0] score_data
        );

          wire feature_buf_valid;
          wire feature_buf_ready;
          wire [{msb}:0] feature_buf_data;
          wire weight_buf_valid;
          wire weight_buf_ready;
          wire [{msb}:0] weight_buf_data;
          wire mac_score_valid;
          wire mac_score_ready;
          wire [{score_msb}:0] mac_score_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_feature_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(feature_valid),
            .in_ready(feature_ready),
            .in_data(feature_data),
            .out_valid(feature_buf_valid),
            .out_ready(feature_buf_ready),
            .out_data(feature_buf_data)
          );

          skid_buffer #(
            .WIDTH({width})
          ) u_weight_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(weight_valid),
            .in_ready(weight_ready),
            .in_data(weight_data),
            .out_valid(weight_buf_valid),
            .out_ready(weight_buf_ready),
            .out_data(weight_buf_data)
          );

          vector_mac_core #(
            .DATA_WIDTH({width}),
            .SCORE_WIDTH({score_width}),
            .VECTOR_LEN(4)
          ) u_vector_mac_core (
            .clk(clk),
            .rst_n(rst_n),
            .feature_valid(feature_buf_valid),
            .feature_ready(feature_buf_ready),
            .feature_data(feature_buf_data),
            .weight_valid(weight_buf_valid),
            .weight_ready(weight_buf_ready),
            .weight_data(weight_buf_data),
            .bias(bias),
            .score_valid(mac_score_valid),
            .score_ready(mac_score_ready),
            .score_data(mac_score_data)
          );

          stream_stage #(
            .WIDTH({score_width})
          ) u_score_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(mac_score_valid),
            .in_ready(mac_score_ready),
            .in_data(mac_score_data),
            .out_valid(score_valid),
            .out_ready(score_ready),
            .out_data(score_data)
          );

        endmodule
        """
    )
    skid_buffer = dedent(
        """\
        module skid_buffer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          reg valid_r;
          reg [WIDTH-1:0] data_r;

          assign in_ready = !valid_r || out_ready;
          assign out_valid = valid_r;
          assign out_data = data_r;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_r <= 1'b0;
              data_r <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              valid_r <= in_valid;
              if (in_valid) begin
                data_r <= in_data;
              end
            end
          end

        endmodule
        """
    )
    vector_mac_core = dedent(
        """\
        module vector_mac_core #(
            parameter DATA_WIDTH = 8,
            parameter SCORE_WIDTH = 16,
            parameter VECTOR_LEN = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire feature_valid,
            output wire feature_ready,
            input wire [DATA_WIDTH-1:0] feature_data,
            input wire weight_valid,
            output wire weight_ready,
            input wire [DATA_WIDTH-1:0] weight_data,
            input wire [SCORE_WIDTH-1:0] bias,
            output reg score_valid,
            input wire score_ready,
            output reg [SCORE_WIDTH-1:0] score_data
        );

          reg [SCORE_WIDTH-1:0] accumulator;
          reg [1:0] vector_index;
          localparam [1:0] LAST_INDEX = VECTOR_LEN - 1;
          wire accept_pair;
          wire [SCORE_WIDTH-1:0] product;
          wire [SCORE_WIDTH-1:0] next_accumulator;

          assign feature_ready = weight_valid && !score_valid;
          assign weight_ready = feature_valid && !score_valid;
          assign accept_pair = feature_valid && feature_ready && weight_valid && weight_ready;
          assign product = feature_data * weight_data;
          assign next_accumulator = accumulator + product;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              accumulator <= {SCORE_WIDTH{1'b0}};
              vector_index <= 2'd0;
              score_valid <= 1'b0;
              score_data <= {SCORE_WIDTH{1'b0}};
            end else begin
              if (score_valid && score_ready) begin
                score_valid <= 1'b0;
              end
              if (accept_pair) begin
                if (vector_index == LAST_INDEX) begin
                  score_data <= next_accumulator + bias;
                  score_valid <= 1'b1;
                  accumulator <= {SCORE_WIDTH{1'b0}};
                  vector_index <= 2'd0;
                end else begin
                  accumulator <= next_accumulator;
                  vector_index <= vector_index + 2'd1;
                end
              end
            end
          end

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output reg out_valid,
            input wire out_ready,
            output reg [WIDTH-1:0] out_data
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              out_data <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                out_data <= in_data;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/vector_mac_core.v": vector_mac_core,
        "rtl/stream_stage.v": stream_stage,
    }


def _composed_td_update_core_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [{msb}:0] reward,
            input wire signed [{msb}:0] value,
            input wire signed [{msb}:0] next_value,
            input wire [{msb}:0] gamma,
            input wire [{msb}:0] alpha,
            output wire out_valid,
            input wire out_ready,
            output wire signed [{msb}:0] td_error,
            output wire signed [{msb}:0] updated_value
        );

          wire input_valid;
          wire input_ready;
          wire signed [{msb}:0] reward_s;
          wire signed [{msb}:0] value_s;
          wire signed [{msb}:0] next_value_s;
          wire [{msb}:0] gamma_s;
          wire [{msb}:0] alpha_s;
          wire discount_valid;
          wire discount_ready;
          wire signed [{msb}:0] discounted_return;
          wire update_valid;
          wire update_ready;
          wire signed [{msb}:0] update_td_error;
          wire signed [{msb}:0] update_value;

          td_input_stage #(
            .DATA_WIDTH({width})
          ) u_td_input_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .reward(reward),
            .value(value),
            .next_value(next_value),
            .gamma(gamma),
            .alpha(alpha),
            .out_valid(input_valid),
            .out_ready(input_ready),
            .reward_out(reward_s),
            .value_out(value_s),
            .next_value_out(next_value_s),
            .gamma_out(gamma_s),
            .alpha_out(alpha_s)
          );

          discount_core #(
            .DATA_WIDTH({width}),
            .SCALE_SHIFT(4)
          ) u_discount_core (
            .in_valid(input_valid),
            .in_ready(input_ready),
            .reward(reward_s),
            .next_value(next_value_s),
            .gamma(gamma_s),
            .out_valid(discount_valid),
            .out_ready(discount_ready),
            .discounted_return(discounted_return)
          );

          td_update_core #(
            .DATA_WIDTH({width}),
            .SCALE_SHIFT(4)
          ) u_td_update_core (
            .in_valid(discount_valid),
            .in_ready(discount_ready),
            .discounted_return(discounted_return),
            .value(value_s),
            .alpha(alpha_s),
            .out_valid(update_valid),
            .out_ready(update_ready),
            .td_error(update_td_error),
            .updated_value(update_value)
          );

          stream_stage #(
            .DATA_WIDTH({width})
          ) u_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(update_valid),
            .in_ready(update_ready),
            .td_error(update_td_error),
            .updated_value(update_value),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .td_error_out(td_error),
            .updated_value_out(updated_value)
          );

        endmodule
        """
    )
    td_input_stage = dedent(
        """\
        module td_input_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [DATA_WIDTH-1:0] reward,
            input wire signed [DATA_WIDTH-1:0] value,
            input wire signed [DATA_WIDTH-1:0] next_value,
            input wire [DATA_WIDTH-1:0] gamma,
            input wire [DATA_WIDTH-1:0] alpha,
            output reg out_valid,
            input wire out_ready,
            output reg signed [DATA_WIDTH-1:0] reward_out,
            output reg signed [DATA_WIDTH-1:0] value_out,
            output reg signed [DATA_WIDTH-1:0] next_value_out,
            output reg [DATA_WIDTH-1:0] gamma_out,
            output reg [DATA_WIDTH-1:0] alpha_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              reward_out <= {DATA_WIDTH{1'b0}};
              value_out <= {DATA_WIDTH{1'b0}};
              next_value_out <= {DATA_WIDTH{1'b0}};
              gamma_out <= {DATA_WIDTH{1'b0}};
              alpha_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                reward_out <= reward;
                value_out <= value;
                next_value_out <= next_value;
                gamma_out <= gamma;
                alpha_out <= alpha;
              end
            end
          end

        endmodule
        """
    )
    discount_core = dedent(
        """\
        module discount_core #(
            parameter DATA_WIDTH = 8,
            parameter SCALE_SHIFT = 4
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire signed [DATA_WIDTH-1:0] reward,
            input wire signed [DATA_WIDTH-1:0] next_value,
            input wire [DATA_WIDTH-1:0] gamma,
            output wire out_valid,
            input wire out_ready,
            output wire signed [DATA_WIDTH-1:0] discounted_return
        );

          wire signed [(2*DATA_WIDTH)-1:0] gamma_next_product;
          wire signed [DATA_WIDTH-1:0] discounted_next;

          assign in_ready = out_ready;
          assign out_valid = in_valid;
          assign gamma_next_product = $signed({1'b0, gamma}) * next_value;
          assign discounted_next = gamma_next_product >>> SCALE_SHIFT;
          assign discounted_return = reward + discounted_next;

        endmodule
        """
    )
    td_update_core = dedent(
        """\
        module td_update_core #(
            parameter DATA_WIDTH = 8,
            parameter SCALE_SHIFT = 4
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire signed [DATA_WIDTH-1:0] discounted_return,
            input wire signed [DATA_WIDTH-1:0] value,
            input wire [DATA_WIDTH-1:0] alpha,
            output wire out_valid,
            input wire out_ready,
            output wire signed [DATA_WIDTH-1:0] td_error,
            output wire signed [DATA_WIDTH-1:0] updated_value
        );

          wire signed [(2*DATA_WIDTH)-1:0] alpha_error_product;
          wire signed [DATA_WIDTH-1:0] scaled_error;

          assign in_ready = out_ready;
          assign out_valid = in_valid;
          assign td_error = discounted_return - value;
          assign alpha_error_product = $signed({1'b0, alpha}) * td_error;
          assign scaled_error = alpha_error_product >>> SCALE_SHIFT;
          assign updated_value = value + scaled_error;

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [DATA_WIDTH-1:0] td_error,
            input wire signed [DATA_WIDTH-1:0] updated_value,
            output reg out_valid,
            input wire out_ready,
            output reg signed [DATA_WIDTH-1:0] td_error_out,
            output reg signed [DATA_WIDTH-1:0] updated_value_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              td_error_out <= {DATA_WIDTH{1'b0}};
              updated_value_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                td_error_out <= td_error;
                updated_value_out <= updated_value;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/td_input_stage.v": td_input_stage,
        "rtl/discount_core.v": discount_core,
        "rtl/td_update_core.v": td_update_core,
        "rtl/stream_stage.v": stream_stage,
    }


def _composed_policy_value_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [{msb}:0] cfg_data,
            input wire obs_valid,
            output wire obs_ready,
            input wire [{msb}:0] obs0,
            input wire [{msb}:0] obs1,
            output wire action_valid,
            input wire action_ready,
            output wire selected_action,
            output wire [{msb}:0] value_estimate
        );

          wire [{msb}:0] weight0;
          wire [{msb}:0] weight1;
          wire [{msb}:0] bias0;
          wire [{msb}:0] bias1;
          wire enable;
          wire obs_stage_valid;
          wire obs_stage_ready;
          wire [{msb}:0] obs0_s;
          wire [{msb}:0] obs1_s;
          wire score_valid;
          wire score_ready;
          wire [{msb}:0] policy_score0;
          wire [{msb}:0] policy_score1;
          wire select_valid;
          wire select_ready;
          wire select_action;
          wire [{msb}:0] select_value;

          config_reg_bank #(
            .DATA_WIDTH({width})
          ) u_config_reg_bank (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .weight0(weight0),
            .weight1(weight1),
            .bias0(bias0),
            .bias1(bias1),
            .enable(enable)
          );

          observation_stage #(
            .DATA_WIDTH({width})
          ) u_observation_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(obs_valid),
            .in_ready(obs_ready),
            .obs0(obs0),
            .obs1(obs1),
            .out_valid(obs_stage_valid),
            .out_ready(obs_stage_ready),
            .obs0_out(obs0_s),
            .obs1_out(obs1_s)
          );

          policy_score_core #(
            .DATA_WIDTH({width})
          ) u_policy_score_core (
            .in_valid(obs_stage_valid),
            .in_ready(obs_stage_ready),
            .obs0(obs0_s),
            .obs1(obs1_s),
            .weight0(weight0),
            .weight1(weight1),
            .bias0(bias0),
            .bias1(bias1),
            .enable(enable),
            .out_valid(score_valid),
            .out_ready(score_ready),
            .score0(policy_score0),
            .score1(policy_score1)
          );

          action_select_core #(
            .DATA_WIDTH({width})
          ) u_action_select_core (
            .in_valid(score_valid),
            .in_ready(score_ready),
            .score0(policy_score0),
            .score1(policy_score1),
            .out_valid(select_valid),
            .out_ready(select_ready),
            .selected_action(select_action),
            .value_estimate(select_value)
          );

          stream_stage #(
            .DATA_WIDTH({width})
          ) u_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(select_valid),
            .in_ready(select_ready),
            .selected_action(select_action),
            .value_estimate(select_value),
            .out_valid(action_valid),
            .out_ready(action_ready),
            .selected_action_out(selected_action),
            .value_estimate_out(value_estimate)
          );

        endmodule
        """
    )
    config_reg_bank = dedent(
        """\
        module config_reg_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [DATA_WIDTH-1:0] cfg_data,
            output reg [DATA_WIDTH-1:0] weight0,
            output reg [DATA_WIDTH-1:0] weight1,
            output reg [DATA_WIDTH-1:0] bias0,
            output reg [DATA_WIDTH-1:0] bias1,
            output reg enable
        );

          assign cfg_ready = 1'b1;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              weight0 <= {{(DATA_WIDTH-1){1'b0}}, 1'b1};
              weight1 <= {{(DATA_WIDTH-1){1'b0}}, 1'b1};
              bias0 <= {DATA_WIDTH{1'b0}};
              bias1 <= {DATA_WIDTH{1'b0}};
              enable <= 1'b0;
            end else if (cfg_valid) begin
              case (cfg_addr)
                3'd0: weight0 <= cfg_data;
                3'd1: bias0 <= cfg_data;
                3'd2: weight1 <= cfg_data;
                3'd3: bias1 <= cfg_data;
                3'd4: enable <= cfg_data[0];
                default: enable <= enable;
              endcase
            end
          end

        endmodule
        """
    )
    observation_stage = dedent(
        """\
        module observation_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            output reg out_valid,
            input wire out_ready,
            output reg [DATA_WIDTH-1:0] obs0_out,
            output reg [DATA_WIDTH-1:0] obs1_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              obs0_out <= {DATA_WIDTH{1'b0}};
              obs1_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                obs0_out <= obs0;
                obs1_out <= obs1;
              end
            end
          end

        endmodule
        """
    )
    policy_score_core = dedent(
        """\
        module policy_score_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            input wire [DATA_WIDTH-1:0] weight0,
            input wire [DATA_WIDTH-1:0] weight1,
            input wire [DATA_WIDTH-1:0] bias0,
            input wire [DATA_WIDTH-1:0] bias1,
            input wire enable,
            output wire out_valid,
            input wire out_ready,
            output wire [DATA_WIDTH-1:0] score0,
            output wire [DATA_WIDTH-1:0] score1
        );

          wire [(2*DATA_WIDTH)-1:0] score0_full;
          wire [(2*DATA_WIDTH)-1:0] score1_full;

          assign in_ready = out_ready;
          assign out_valid = in_valid;
          assign score0_full = (obs0 * weight0) + bias0;
          assign score1_full = (obs1 * weight1) + bias1;
          assign score0 = enable ? score0_full[DATA_WIDTH-1:0] : {DATA_WIDTH{1'b0}};
          assign score1 = enable ? score1_full[DATA_WIDTH-1:0] : {DATA_WIDTH{1'b0}};

        endmodule
        """
    )
    action_select_core = dedent(
        """\
        module action_select_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] score0,
            input wire [DATA_WIDTH-1:0] score1,
            output wire out_valid,
            input wire out_ready,
            output wire selected_action,
            output wire [DATA_WIDTH-1:0] value_estimate
        );

          wire [DATA_WIDTH:0] score_sum;

          assign in_ready = out_ready;
          assign out_valid = in_valid;
          assign selected_action = score1 > score0;
          assign score_sum = {1'b0, score0} + {1'b0, score1};
          assign value_estimate = score_sum[DATA_WIDTH:1];

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire selected_action,
            input wire [DATA_WIDTH-1:0] value_estimate,
            output reg out_valid,
            input wire out_ready,
            output reg selected_action_out,
            output reg [DATA_WIDTH-1:0] value_estimate_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              selected_action_out <= 1'b0;
              value_estimate_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                selected_action_out <= selected_action;
                value_estimate_out <= value_estimate;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/config_reg_bank.v": config_reg_bank,
        "rtl/observation_stage.v": observation_stage,
        "rtl/policy_score_core.v": policy_score_core,
        "rtl/action_select_core.v": action_select_core,
        "rtl/stream_stage.v": stream_stage,
    }


def _composed_replay_sample_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire host_valid,
            output wire host_ready,
            input wire [{msb}:0] host_state,
            input wire host_action,
            input wire [{msb}:0] host_reward,
            input wire [{msb}:0] host_next_state,
            input wire host_done,
            output wire sample_valid,
            input wire sample_ready,
            output wire [{msb}:0] sample_state,
            output wire sample_action,
            output wire [{msb}:0] sample_reward,
            output wire [{msb}:0] sample_next_state,
            output wire sample_done,
            output wire [2:0] occupancy
        );

          wire host_stage_valid;
          wire host_stage_ready;
          wire [{msb}:0] host_stage_state;
          wire host_stage_action;
          wire [{msb}:0] host_stage_reward;
          wire [{msb}:0] host_stage_next_state;
          wire host_stage_done;
          wire store_read_valid;
          wire store_read_ready;
          wire [{msb}:0] store_read_state;
          wire store_read_action;
          wire [{msb}:0] store_read_reward;
          wire [{msb}:0] store_read_next_state;
          wire store_read_done;
          wire [{msb}:0] sample_pack_state;
          wire sample_pack_action;
          wire [{msb}:0] sample_pack_reward;
          wire [{msb}:0] sample_pack_next_state;
          wire sample_pack_done;
          wire [2:0] store_occupancy;

          host_sample_stage #(
            .DATA_WIDTH({width})
          ) u_host_sample_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(host_valid),
            .in_ready(host_ready),
            .state(host_state),
            .action(host_action),
            .reward(host_reward),
            .next_state(host_next_state),
            .done(host_done),
            .out_valid(host_stage_valid),
            .out_ready(host_stage_ready),
            .state_out(host_stage_state),
            .action_out(host_stage_action),
            .reward_out(host_stage_reward),
            .next_state_out(host_stage_next_state),
            .done_out(host_stage_done)
          );

          replay_store #(
            .DATA_WIDTH({width}),
            .DEPTH(4)
          ) u_replay_store (
            .clk(clk),
            .rst_n(rst_n),
            .write_valid(host_stage_valid),
            .write_ready(host_stage_ready),
            .write_state(host_stage_state),
            .write_action(host_stage_action),
            .write_reward(host_stage_reward),
            .write_next_state(host_stage_next_state),
            .write_done(host_stage_done),
            .read_valid(store_read_valid),
            .read_ready(store_read_ready),
            .read_state(store_read_state),
            .read_action(store_read_action),
            .read_reward(store_read_reward),
            .read_next_state(store_read_next_state),
            .read_done(store_read_done),
            .occupancy(store_occupancy)
          );

          sample_pack_core #(
            .DATA_WIDTH({width})
          ) u_sample_pack_core (
            .state(store_read_state),
            .action(store_read_action),
            .reward(store_read_reward),
            .next_state(store_read_next_state),
            .done(store_read_done),
            .sample_state(sample_pack_state),
            .sample_action(sample_pack_action),
            .sample_reward(sample_pack_reward),
            .sample_next_state(sample_pack_next_state),
            .sample_done(sample_pack_done)
          );

          sample_read_stage #(
            .DATA_WIDTH({width})
          ) u_sample_read_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(store_read_valid),
            .read_ready(store_read_ready),
            .sample_state(sample_pack_state),
            .sample_action(sample_pack_action),
            .sample_reward(sample_pack_reward),
            .sample_next_state(sample_pack_next_state),
            .sample_done(sample_pack_done),
            .out_valid(sample_valid),
            .out_ready(sample_ready),
            .sample_state_out(sample_state),
            .sample_action_out(sample_action),
            .sample_reward_out(sample_reward),
            .sample_next_state_out(sample_next_state),
            .sample_done_out(sample_done)
          );

          occupancy_counter u_occupancy_counter (
            .occupancy_in(store_occupancy),
            .occupancy_out(occupancy)
          );

        endmodule
        """
    )
    host_sample_stage = dedent(
        """\
        module host_sample_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] state,
            input wire action,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_state,
            input wire done,
            output reg out_valid,
            input wire out_ready,
            output reg [DATA_WIDTH-1:0] state_out,
            output reg action_out,
            output reg [DATA_WIDTH-1:0] reward_out,
            output reg [DATA_WIDTH-1:0] next_state_out,
            output reg done_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              state_out <= {DATA_WIDTH{1'b0}};
              action_out <= 1'b0;
              reward_out <= {DATA_WIDTH{1'b0}};
              next_state_out <= {DATA_WIDTH{1'b0}};
              done_out <= 1'b0;
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                state_out <= state;
                action_out <= action;
                reward_out <= reward;
                next_state_out <= next_state;
                done_out <= done;
              end
            end
          end

        endmodule
        """
    )
    replay_store = dedent(
        """\
        module replay_store #(
            parameter DATA_WIDTH = 8,
            parameter DEPTH = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire write_valid,
            output wire write_ready,
            input wire [DATA_WIDTH-1:0] write_state,
            input wire write_action,
            input wire [DATA_WIDTH-1:0] write_reward,
            input wire [DATA_WIDTH-1:0] write_next_state,
            input wire write_done,
            output wire read_valid,
            input wire read_ready,
            output wire [DATA_WIDTH-1:0] read_state,
            output wire read_action,
            output wire [DATA_WIDTH-1:0] read_reward,
            output wire [DATA_WIDTH-1:0] read_next_state,
            output wire read_done,
            output reg [2:0] occupancy
        );

          reg [DATA_WIDTH-1:0] state_mem [0:DEPTH-1];
          reg action_mem [0:DEPTH-1];
          reg [DATA_WIDTH-1:0] reward_mem [0:DEPTH-1];
          reg [DATA_WIDTH-1:0] next_state_mem [0:DEPTH-1];
          reg done_mem [0:DEPTH-1];
          reg [1:0] write_ptr;
          reg [1:0] read_ptr;
          wire write_fire;
          wire read_fire;

          assign write_ready = occupancy < 3'd4;
          assign read_valid = occupancy != 3'd0;
          assign write_fire = write_valid && write_ready;
          assign read_fire = read_valid && read_ready;
          assign read_state = state_mem[read_ptr];
          assign read_action = action_mem[read_ptr];
          assign read_reward = reward_mem[read_ptr];
          assign read_next_state = next_state_mem[read_ptr];
          assign read_done = done_mem[read_ptr];

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              write_ptr <= 2'd0;
              read_ptr <= 2'd0;
              occupancy <= 3'd0;
              state_mem[0] <= {DATA_WIDTH{1'b0}};
              state_mem[1] <= {DATA_WIDTH{1'b0}};
              state_mem[2] <= {DATA_WIDTH{1'b0}};
              state_mem[3] <= {DATA_WIDTH{1'b0}};
              action_mem[0] <= 1'b0;
              action_mem[1] <= 1'b0;
              action_mem[2] <= 1'b0;
              action_mem[3] <= 1'b0;
              reward_mem[0] <= {DATA_WIDTH{1'b0}};
              reward_mem[1] <= {DATA_WIDTH{1'b0}};
              reward_mem[2] <= {DATA_WIDTH{1'b0}};
              reward_mem[3] <= {DATA_WIDTH{1'b0}};
              next_state_mem[0] <= {DATA_WIDTH{1'b0}};
              next_state_mem[1] <= {DATA_WIDTH{1'b0}};
              next_state_mem[2] <= {DATA_WIDTH{1'b0}};
              next_state_mem[3] <= {DATA_WIDTH{1'b0}};
              done_mem[0] <= 1'b0;
              done_mem[1] <= 1'b0;
              done_mem[2] <= 1'b0;
              done_mem[3] <= 1'b0;
            end else begin
              if (write_fire) begin
                state_mem[write_ptr] <= write_state;
                action_mem[write_ptr] <= write_action;
                reward_mem[write_ptr] <= write_reward;
                next_state_mem[write_ptr] <= write_next_state;
                done_mem[write_ptr] <= write_done;
                write_ptr <= write_ptr + 2'd1;
              end
              if (read_fire) begin
                read_ptr <= read_ptr + 2'd1;
              end
              if (write_fire && !read_fire) begin
                occupancy <= occupancy + 3'd1;
              end else if (!write_fire && read_fire) begin
                occupancy <= occupancy - 3'd1;
              end
            end
          end

        endmodule
        """
    )
    sample_pack_core = dedent(
        """\
        module sample_pack_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire [DATA_WIDTH-1:0] state,
            input wire action,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_state,
            input wire done,
            output wire [DATA_WIDTH-1:0] sample_state,
            output wire sample_action,
            output wire [DATA_WIDTH-1:0] sample_reward,
            output wire [DATA_WIDTH-1:0] sample_next_state,
            output wire sample_done
        );

          assign sample_state = state;
          assign sample_action = action;
          assign sample_reward = reward;
          assign sample_next_state = next_state;
          assign sample_done = done;

        endmodule
        """
    )
    sample_read_stage = dedent(
        """\
        module sample_read_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire read_ready,
            input wire [DATA_WIDTH-1:0] sample_state,
            input wire sample_action,
            input wire [DATA_WIDTH-1:0] sample_reward,
            input wire [DATA_WIDTH-1:0] sample_next_state,
            input wire sample_done,
            output reg out_valid,
            input wire out_ready,
            output reg [DATA_WIDTH-1:0] sample_state_out,
            output reg sample_action_out,
            output reg [DATA_WIDTH-1:0] sample_reward_out,
            output reg [DATA_WIDTH-1:0] sample_next_state_out,
            output reg sample_done_out
        );

          assign read_ready = out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              sample_state_out <= {DATA_WIDTH{1'b0}};
              sample_action_out <= 1'b0;
              sample_reward_out <= {DATA_WIDTH{1'b0}};
              sample_next_state_out <= {DATA_WIDTH{1'b0}};
              sample_done_out <= 1'b0;
            end else if (read_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                sample_state_out <= sample_state;
                sample_action_out <= sample_action;
                sample_reward_out <= sample_reward;
                sample_next_state_out <= sample_next_state;
                sample_done_out <= sample_done;
              end
            end
          end

        endmodule
        """
    )
    occupancy_counter = dedent(
        """\
        module occupancy_counter (
            input wire [2:0] occupancy_in,
            output wire [2:0] occupancy_out
        );

          assign occupancy_out = occupancy_in;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/host_sample_stage.v": host_sample_stage,
        "rtl/replay_store.v": replay_store,
        "rtl/sample_pack_core.v": sample_pack_core,
        "rtl/sample_read_stage.v": sample_read_stage,
        "rtl/occupancy_counter.v": occupancy_counter,
    }


def _composed_host_protocol_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    stream_msb = width * 2 - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire s_axi_awvalid,
            output wire s_axi_awready,
            input wire [3:0] s_axi_awaddr,
            input wire s_axi_wvalid,
            output wire s_axi_wready,
            input wire [{msb}:0] s_axi_wdata,
            input wire s_axi_wstrb,
            output wire s_axi_bvalid,
            input wire s_axi_bready,
            input wire s_axi_arvalid,
            output wire s_axi_arready,
            input wire [3:0] s_axi_araddr,
            output wire s_axi_rvalid,
            input wire s_axi_rready,
            output wire [{msb}:0] s_axi_rdata,
            output wire m_axis_tvalid,
            input wire m_axis_tready,
            output wire [{stream_msb}:0] m_axis_tdata,
            output wire m_axis_tlast,
            output wire irq
        );

          wire write_valid;
          wire [3:0] write_addr;
          wire [{msb}:0] write_data;
          wire read_valid;
          wire [3:0] read_addr;
          wire start_pulse;
          wire [{msb}:0] sample0;
          wire [{msb}:0] sample1;
          wire stream_done;
          wire irq_state;

          axi_lite_write_ctrl #(
            .DATA_WIDTH({width})
          ) u_axi_lite_write_ctrl (
            .clk(clk),
            .rst_n(rst_n),
            .awvalid(s_axi_awvalid),
            .awready(s_axi_awready),
            .awaddr(s_axi_awaddr),
            .wvalid(s_axi_wvalid),
            .wready(s_axi_wready),
            .wdata(s_axi_wdata),
            .wstrb(s_axi_wstrb),
            .bvalid(s_axi_bvalid),
            .bready(s_axi_bready),
            .write_valid(write_valid),
            .write_addr(write_addr),
            .write_data(write_data)
          );

          axi_lite_read_ctrl u_axi_lite_read_ctrl (
            .clk(clk),
            .rst_n(rst_n),
            .arvalid(s_axi_arvalid),
            .arready(s_axi_arready),
            .araddr(s_axi_araddr),
            .rvalid(s_axi_rvalid),
            .rready(s_axi_rready),
            .read_valid(read_valid),
            .read_addr(read_addr)
          );

          control_reg_bank #(
            .DATA_WIDTH({width})
          ) u_control_reg_bank (
            .clk(clk),
            .rst_n(rst_n),
            .write_valid(write_valid),
            .write_addr(write_addr),
            .write_data(write_data),
            .read_valid(read_valid),
            .read_addr(read_addr),
            .read_data(s_axi_rdata),
            .stream_done(stream_done),
            .start_pulse(start_pulse),
            .sample0(sample0),
            .sample1(sample1),
            .irq_state(irq_state)
          );

          sample_stream_adapter #(
            .DATA_WIDTH({width})
          ) u_sample_stream_adapter (
            .clk(clk),
            .rst_n(rst_n),
            .start(start_pulse),
            .sample0(sample0),
            .sample1(sample1),
            .tvalid(m_axis_tvalid),
            .tready(m_axis_tready),
            .tdata(m_axis_tdata),
            .tlast(m_axis_tlast),
            .stream_done(stream_done)
          );

          irq_status u_irq_status (
            .irq_in(irq_state),
            .irq_out(irq)
          );

        endmodule
        """
    )
    axi_lite_write_ctrl = dedent(
        """\
        module axi_lite_write_ctrl #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire awvalid,
            output wire awready,
            input wire [3:0] awaddr,
            input wire wvalid,
            output wire wready,
            input wire [DATA_WIDTH-1:0] wdata,
            input wire wstrb,
            output reg bvalid,
            input wire bready,
            output wire write_valid,
            output wire [3:0] write_addr,
            output wire [DATA_WIDTH-1:0] write_data
        );

          wire accept_write;

          assign awready = !bvalid;
          assign wready = !bvalid;
          assign accept_write = awvalid && wvalid && awready && wready && wstrb;
          assign write_valid = accept_write;
          assign write_addr = awaddr;
          assign write_data = wdata;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              bvalid <= 1'b0;
            end else begin
              if (accept_write) begin
                bvalid <= 1'b1;
              end else if (bvalid && bready) begin
                bvalid <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    axi_lite_read_ctrl = dedent(
        """\
        module axi_lite_read_ctrl (
            input wire clk,
            input wire rst_n,
            input wire arvalid,
            output wire arready,
            input wire [3:0] araddr,
            output reg rvalid,
            input wire rready,
            output wire read_valid,
            output wire [3:0] read_addr
        );

          wire accept_read;

          assign arready = !rvalid;
          assign accept_read = arvalid && arready;
          assign read_valid = accept_read;
          assign read_addr = araddr;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              rvalid <= 1'b0;
            end else begin
              if (accept_read) begin
                rvalid <= 1'b1;
              end else if (rvalid && rready) begin
                rvalid <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    control_reg_bank = dedent(
        """\
        module control_reg_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire write_valid,
            input wire [3:0] write_addr,
            input wire [DATA_WIDTH-1:0] write_data,
            input wire read_valid,
            input wire [3:0] read_addr,
            output reg [DATA_WIDTH-1:0] read_data,
            input wire stream_done,
            output reg start_pulse,
            output reg [DATA_WIDTH-1:0] sample0,
            output reg [DATA_WIDTH-1:0] sample1,
            output reg irq_state
        );

          reg [DATA_WIDTH-1:0] ctrl;
          reg busy;
          reg done;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              ctrl <= {DATA_WIDTH{1'b0}};
              sample0 <= {DATA_WIDTH{1'b0}};
              sample1 <= {DATA_WIDTH{1'b0}};
              busy <= 1'b0;
              done <= 1'b0;
              irq_state <= 1'b0;
              start_pulse <= 1'b0;
              read_data <= {DATA_WIDTH{1'b0}};
            end else begin
              start_pulse <= 1'b0;
              if (write_valid) begin
                case (write_addr)
                  4'h0: begin
                    ctrl <= write_data;
                    if (write_data[0]) begin
                      start_pulse <= 1'b1;
                      busy <= 1'b1;
                      done <= 1'b0;
                    end
                    if (write_data[1]) begin
                      irq_state <= 1'b0;
                    end
                  end
                  4'h4: sample0 <= write_data;
                  4'h8: sample1 <= write_data;
                  default: ctrl <= ctrl;
                endcase
              end
              if (stream_done) begin
                busy <= 1'b0;
                done <= 1'b1;
                irq_state <= 1'b1;
              end
              if (read_valid) begin
                case (read_addr)
                  4'h0: read_data <= ctrl;
                  4'h4: read_data <= sample0;
                  4'h8: read_data <= sample1;
                  4'hc: read_data <= {{(DATA_WIDTH-3){1'b0}}, irq_state, done, busy};
                  default: read_data <= {DATA_WIDTH{1'b0}};
                endcase
              end
            end
          end

        endmodule
        """
    )
    sample_stream_adapter = dedent(
        """\
        module sample_stream_adapter #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [DATA_WIDTH-1:0] sample0,
            input wire [DATA_WIDTH-1:0] sample1,
            output reg tvalid,
            input wire tready,
            output reg [(2*DATA_WIDTH)-1:0] tdata,
            output reg tlast,
            output reg stream_done
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              tvalid <= 1'b0;
              tdata <= {(2*DATA_WIDTH){1'b0}};
              tlast <= 1'b0;
              stream_done <= 1'b0;
            end else begin
              stream_done <= 1'b0;
              if (start && !tvalid) begin
                tvalid <= 1'b1;
                tdata <= {sample1, sample0};
                tlast <= 1'b1;
              end else if (tvalid && tready) begin
                tvalid <= 1'b0;
                tlast <= 1'b0;
                stream_done <= 1'b1;
              end
            end
          end

        endmodule
        """
    )
    irq_status = dedent(
        """\
        module irq_status (
            input wire irq_in,
            output wire irq_out
        );

          assign irq_out = irq_in;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/axi_lite_write_ctrl.v": axi_lite_write_ctrl,
        "rtl/axi_lite_read_ctrl.v": axi_lite_read_ctrl,
        "rtl/control_reg_bank.v": control_reg_bank,
        "rtl/sample_stream_adapter.v": sample_stream_adapter,
        "rtl/irq_status.v": irq_status,
    }


def _composed_rl_accelerator_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [{msb}:0] cfg_data,
            input wire sample_valid,
            output wire sample_ready,
            input wire [{msb}:0] obs0,
            input wire [{msb}:0] obs1,
            input wire [{msb}:0] reward,
            input wire [{msb}:0] next_value,
            input wire done_in,
            output wire result_valid,
            input wire result_ready,
            output wire selected_action,
            output wire [{msb}:0] value_estimate,
            output wire [{msb}:0] updated_value,
            output wire episode_done,
            output wire irq
        );

          wire [{msb}:0] weight0;
          wire [{msb}:0] bias0;
          wire [{msb}:0] weight1;
          wire [{msb}:0] bias1;
          wire [{msb}:0] alpha;
          wire enable;
          wire sample_stage_valid;
          wire sample_consume_ready;
          wire [{msb}:0] captured_obs0;
          wire [{msb}:0] captured_obs1;
          wire [{msb}:0] captured_reward;
          wire [{msb}:0] captured_next_value;
          wire captured_done;
          wire policy_valid;
          wire policy_selected_action;
          wire [{msb}:0] policy_value_estimate;
          wire update_valid;
          wire [{msb}:0] update_updated_value;

          host_config_bank #(
            .DATA_WIDTH({width})
          ) u_host_config_bank (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .alpha(alpha),
            .enable(enable)
          );

          sample_capture_stage #(
            .DATA_WIDTH({width})
          ) u_sample_capture_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(sample_valid),
            .in_ready(sample_ready),
            .obs0(obs0),
            .obs1(obs1),
            .reward(reward),
            .next_value(next_value),
            .done_in(done_in),
            .consume_ready(sample_consume_ready),
            .out_valid(sample_stage_valid),
            .obs0_out(captured_obs0),
            .obs1_out(captured_obs1),
            .reward_out(captured_reward),
            .next_value_out(captured_next_value),
            .done_out(captured_done)
          );

          policy_value_core #(
            .DATA_WIDTH({width})
          ) u_policy_value_core (
            .in_valid(sample_stage_valid),
            .obs0(captured_obs0),
            .obs1(captured_obs1),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .enable(enable),
            .out_valid(policy_valid),
            .selected_action(policy_selected_action),
            .value_estimate(policy_value_estimate)
          );

          td_update_core #(
            .DATA_WIDTH({width})
          ) u_td_update_core (
            .in_valid(policy_valid),
            .reward(captured_reward),
            .next_value(captured_next_value),
            .value_estimate(policy_value_estimate),
            .alpha(alpha),
            .out_valid(update_valid),
            .updated_value(update_updated_value)
          );

          result_stream_stage #(
            .DATA_WIDTH({width})
          ) u_result_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(update_valid),
            .out_ready(sample_consume_ready),
            .selected_action(policy_selected_action),
            .value_estimate(policy_value_estimate),
            .updated_value(update_updated_value),
            .done_in(captured_done),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action_out(selected_action),
            .value_estimate_out(value_estimate),
            .updated_value_out(updated_value),
            .episode_done_out(episode_done),
            .irq(irq)
          );

        endmodule
        """
    )
    host_config_bank = dedent(
        """\
        module host_config_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [DATA_WIDTH-1:0] cfg_data,
            output reg [DATA_WIDTH-1:0] weight0,
            output reg [DATA_WIDTH-1:0] bias0,
            output reg [DATA_WIDTH-1:0] weight1,
            output reg [DATA_WIDTH-1:0] bias1,
            output reg [DATA_WIDTH-1:0] alpha,
            output reg enable
        );

          assign cfg_ready = 1'b1;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              weight0 <= {DATA_WIDTH{1'b0}};
              bias0 <= {DATA_WIDTH{1'b0}};
              weight1 <= {DATA_WIDTH{1'b0}};
              bias1 <= {DATA_WIDTH{1'b0}};
              alpha <= {DATA_WIDTH{1'b0}};
              enable <= 1'b0;
            end else if (cfg_valid && cfg_ready) begin
              case (cfg_addr)
                3'd0: weight0 <= cfg_data;
                3'd1: bias0 <= cfg_data;
                3'd2: weight1 <= cfg_data;
                3'd3: bias1 <= cfg_data;
                3'd4: alpha <= cfg_data;
                3'd5: enable <= cfg_data[0];
                default: enable <= enable;
              endcase
            end
          end

        endmodule
        """
    )
    sample_capture_stage = dedent(
        """\
        module sample_capture_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_value,
            input wire done_in,
            input wire consume_ready,
            output wire out_valid,
            output reg [DATA_WIDTH-1:0] obs0_out,
            output reg [DATA_WIDTH-1:0] obs1_out,
            output reg [DATA_WIDTH-1:0] reward_out,
            output reg [DATA_WIDTH-1:0] next_value_out,
            output reg done_out
        );

          reg valid_reg;

          assign in_ready = !valid_reg || consume_ready;
          assign out_valid = valid_reg;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_reg <= 1'b0;
              obs0_out <= {DATA_WIDTH{1'b0}};
              obs1_out <= {DATA_WIDTH{1'b0}};
              reward_out <= {DATA_WIDTH{1'b0}};
              next_value_out <= {DATA_WIDTH{1'b0}};
              done_out <= 1'b0;
            end else begin
              if (in_valid && in_ready) begin
                valid_reg <= 1'b1;
                obs0_out <= obs0;
                obs1_out <= obs1;
                reward_out <= reward;
                next_value_out <= next_value;
                done_out <= done_in;
              end else if (consume_ready) begin
                valid_reg <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    policy_value_core = dedent(
        """\
        module policy_value_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            input wire [DATA_WIDTH-1:0] weight0,
            input wire [DATA_WIDTH-1:0] bias0,
            input wire [DATA_WIDTH-1:0] weight1,
            input wire [DATA_WIDTH-1:0] bias1,
            input wire enable,
            output wire out_valid,
            output wire selected_action,
            output wire [DATA_WIDTH-1:0] value_estimate
        );

          wire [(2*DATA_WIDTH):0] score0_full;
          wire [(2*DATA_WIDTH):0] score1_full;
          wire [DATA_WIDTH-1:0] score0;
          wire [DATA_WIDTH-1:0] score1;
          wire [DATA_WIDTH:0] value_sum;

          assign score0_full = (obs0 * weight0) + bias0;
          assign score1_full = (obs1 * weight1) + bias1;
          assign score0 = score0_full[DATA_WIDTH-1:0];
          assign score1 = score1_full[DATA_WIDTH-1:0];
          assign value_sum = {1'b0, score0} + {1'b0, score1};
          assign selected_action = score1 > score0;
          assign value_estimate = value_sum[DATA_WIDTH:1];
          assign out_valid = in_valid && enable;

        endmodule
        """
    )
    td_update_core = dedent(
        """\
        module td_update_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_value,
            input wire [DATA_WIDTH-1:0] value_estimate,
            input wire [DATA_WIDTH-1:0] alpha,
            output wire out_valid,
            output wire [DATA_WIDTH-1:0] updated_value
        );

          wire [DATA_WIDTH:0] td_error_full;
          wire [(2*DATA_WIDTH)-1:0] update_product;
          wire [DATA_WIDTH-1:0] update_delta;

          assign td_error_full = {1'b0, reward} + {1'b0, next_value} - {1'b0, value_estimate};
          assign update_product = alpha * td_error_full[DATA_WIDTH-1:0];
          assign update_delta = update_product[(2*DATA_WIDTH)-1:4];
          assign updated_value = value_estimate + update_delta;
          assign out_valid = in_valid;

        endmodule
        """
    )
    result_stream_stage = dedent(
        """\
        module result_stream_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire out_ready,
            input wire selected_action,
            input wire [DATA_WIDTH-1:0] value_estimate,
            input wire [DATA_WIDTH-1:0] updated_value,
            input wire done_in,
            output reg result_valid,
            input wire result_ready,
            output reg selected_action_out,
            output reg [DATA_WIDTH-1:0] value_estimate_out,
            output reg [DATA_WIDTH-1:0] updated_value_out,
            output reg episode_done_out,
            output reg irq
        );

          assign out_ready = !result_valid || result_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              result_valid <= 1'b0;
              selected_action_out <= 1'b0;
              value_estimate_out <= {DATA_WIDTH{1'b0}};
              updated_value_out <= {DATA_WIDTH{1'b0}};
              episode_done_out <= 1'b0;
              irq <= 1'b0;
            end else begin
              if (result_valid && result_ready) begin
                if (episode_done_out) begin
                  irq <= 1'b1;
                end
                result_valid <= 1'b0;
              end
              if (in_valid && out_ready) begin
                result_valid <= 1'b1;
                selected_action_out <= selected_action;
                value_estimate_out <= value_estimate;
                updated_value_out <= updated_value;
                episode_done_out <= done_in;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/host_config_bank.v": host_config_bank,
        "rtl/sample_capture_stage.v": sample_capture_stage,
        "rtl/policy_value_core.v": policy_value_core,
        "rtl/td_update_core.v": td_update_core,
        "rtl/result_stream_stage.v": result_stream_stage,
    }


def _composed_batch_rl_accelerator_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [{msb}:0] cfg_data,
            input wire batch_valid,
            output wire batch_ready,
            input wire [{msb}:0] obs0_a,
            input wire [{msb}:0] obs1_a,
            input wire [{msb}:0] reward_a,
            input wire [{msb}:0] next_value_a,
            input wire done_a,
            input wire [{msb}:0] obs0_b,
            input wire [{msb}:0] obs1_b,
            input wire [{msb}:0] reward_b,
            input wire [{msb}:0] next_value_b,
            input wire done_b,
            output wire result_valid,
            input wire result_ready,
            output wire selected_action_a,
            output wire [{msb}:0] value_estimate_a,
            output wire [{msb}:0] updated_value_a,
            output wire selected_action_b,
            output wire [{msb}:0] value_estimate_b,
            output wire [{msb}:0] updated_value_b,
            output wire batch_done,
            output wire irq
        );

          wire [{msb}:0] weight0;
          wire [{msb}:0] bias0;
          wire [{msb}:0] weight1;
          wire [{msb}:0] bias1;
          wire [{msb}:0] alpha;
          wire enable;
          wire batch_stage_valid;
          wire batch_consume_ready;
          wire [{msb}:0] captured_obs0_a;
          wire [{msb}:0] captured_obs1_a;
          wire [{msb}:0] captured_reward_a;
          wire [{msb}:0] captured_next_value_a;
          wire captured_done_a;
          wire [{msb}:0] captured_obs0_b;
          wire [{msb}:0] captured_obs1_b;
          wire [{msb}:0] captured_reward_b;
          wire [{msb}:0] captured_next_value_b;
          wire captured_done_b;
          wire policy_valid;
          wire policy_selected_action_a;
          wire [{msb}:0] policy_value_estimate_a;
          wire policy_selected_action_b;
          wire [{msb}:0] policy_value_estimate_b;
          wire update_valid;
          wire [{msb}:0] update_updated_value_a;
          wire [{msb}:0] update_updated_value_b;

          batch_config_bank #(
            .DATA_WIDTH({width})
          ) u_batch_config_bank (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .alpha(alpha),
            .enable(enable)
          );

          batch_sample_buffer #(
            .DATA_WIDTH({width})
          ) u_batch_sample_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(batch_valid),
            .in_ready(batch_ready),
            .obs0_a(obs0_a),
            .obs1_a(obs1_a),
            .reward_a(reward_a),
            .next_value_a(next_value_a),
            .done_a(done_a),
            .obs0_b(obs0_b),
            .obs1_b(obs1_b),
            .reward_b(reward_b),
            .next_value_b(next_value_b),
            .done_b(done_b),
            .consume_ready(batch_consume_ready),
            .out_valid(batch_stage_valid),
            .obs0_a_out(captured_obs0_a),
            .obs1_a_out(captured_obs1_a),
            .reward_a_out(captured_reward_a),
            .next_value_a_out(captured_next_value_a),
            .done_a_out(captured_done_a),
            .obs0_b_out(captured_obs0_b),
            .obs1_b_out(captured_obs1_b),
            .reward_b_out(captured_reward_b),
            .next_value_b_out(captured_next_value_b),
            .done_b_out(captured_done_b)
          );

          dual_policy_value_core #(
            .DATA_WIDTH({width})
          ) u_dual_policy_value_core (
            .in_valid(batch_stage_valid),
            .obs0_a(captured_obs0_a),
            .obs1_a(captured_obs1_a),
            .obs0_b(captured_obs0_b),
            .obs1_b(captured_obs1_b),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .enable(enable),
            .out_valid(policy_valid),
            .selected_action_a(policy_selected_action_a),
            .value_estimate_a(policy_value_estimate_a),
            .selected_action_b(policy_selected_action_b),
            .value_estimate_b(policy_value_estimate_b)
          );

          dual_td_update_core #(
            .DATA_WIDTH({width})
          ) u_dual_td_update_core (
            .in_valid(policy_valid),
            .reward_a(captured_reward_a),
            .next_value_a(captured_next_value_a),
            .value_estimate_a(policy_value_estimate_a),
            .reward_b(captured_reward_b),
            .next_value_b(captured_next_value_b),
            .value_estimate_b(policy_value_estimate_b),
            .alpha(alpha),
            .out_valid(update_valid),
            .updated_value_a(update_updated_value_a),
            .updated_value_b(update_updated_value_b)
          );

          batch_result_stage #(
            .DATA_WIDTH({width})
          ) u_batch_result_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(update_valid),
            .out_ready(batch_consume_ready),
            .selected_action_a(policy_selected_action_a),
            .value_estimate_a(policy_value_estimate_a),
            .updated_value_a(update_updated_value_a),
            .selected_action_b(policy_selected_action_b),
            .value_estimate_b(policy_value_estimate_b),
            .updated_value_b(update_updated_value_b),
            .done_a(captured_done_a),
            .done_b(captured_done_b),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action_a_out(selected_action_a),
            .value_estimate_a_out(value_estimate_a),
            .updated_value_a_out(updated_value_a),
            .selected_action_b_out(selected_action_b),
            .value_estimate_b_out(value_estimate_b),
            .updated_value_b_out(updated_value_b),
            .batch_done_out(batch_done),
            .irq(irq)
          );

        endmodule
        """
    )
    batch_config_bank = _batch_config_bank_rtl()
    batch_sample_buffer = dedent(
        """\
        module batch_sample_buffer #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0_a,
            input wire [DATA_WIDTH-1:0] obs1_a,
            input wire [DATA_WIDTH-1:0] reward_a,
            input wire [DATA_WIDTH-1:0] next_value_a,
            input wire done_a,
            input wire [DATA_WIDTH-1:0] obs0_b,
            input wire [DATA_WIDTH-1:0] obs1_b,
            input wire [DATA_WIDTH-1:0] reward_b,
            input wire [DATA_WIDTH-1:0] next_value_b,
            input wire done_b,
            input wire consume_ready,
            output wire out_valid,
            output reg [DATA_WIDTH-1:0] obs0_a_out,
            output reg [DATA_WIDTH-1:0] obs1_a_out,
            output reg [DATA_WIDTH-1:0] reward_a_out,
            output reg [DATA_WIDTH-1:0] next_value_a_out,
            output reg done_a_out,
            output reg [DATA_WIDTH-1:0] obs0_b_out,
            output reg [DATA_WIDTH-1:0] obs1_b_out,
            output reg [DATA_WIDTH-1:0] reward_b_out,
            output reg [DATA_WIDTH-1:0] next_value_b_out,
            output reg done_b_out
        );

          reg valid_reg;

          assign in_ready = !valid_reg || consume_ready;
          assign out_valid = valid_reg;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_reg <= 1'b0;
              obs0_a_out <= {DATA_WIDTH{1'b0}};
              obs1_a_out <= {DATA_WIDTH{1'b0}};
              reward_a_out <= {DATA_WIDTH{1'b0}};
              next_value_a_out <= {DATA_WIDTH{1'b0}};
              done_a_out <= 1'b0;
              obs0_b_out <= {DATA_WIDTH{1'b0}};
              obs1_b_out <= {DATA_WIDTH{1'b0}};
              reward_b_out <= {DATA_WIDTH{1'b0}};
              next_value_b_out <= {DATA_WIDTH{1'b0}};
              done_b_out <= 1'b0;
            end else begin
              if (in_valid && in_ready) begin
                valid_reg <= 1'b1;
                obs0_a_out <= obs0_a;
                obs1_a_out <= obs1_a;
                reward_a_out <= reward_a;
                next_value_a_out <= next_value_a;
                done_a_out <= done_a;
                obs0_b_out <= obs0_b;
                obs1_b_out <= obs1_b;
                reward_b_out <= reward_b;
                next_value_b_out <= next_value_b;
                done_b_out <= done_b;
              end else if (consume_ready) begin
                valid_reg <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    dual_policy_value_core = dedent(
        """\
        module dual_policy_value_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] obs0_a,
            input wire [DATA_WIDTH-1:0] obs1_a,
            input wire [DATA_WIDTH-1:0] obs0_b,
            input wire [DATA_WIDTH-1:0] obs1_b,
            input wire [DATA_WIDTH-1:0] weight0,
            input wire [DATA_WIDTH-1:0] bias0,
            input wire [DATA_WIDTH-1:0] weight1,
            input wire [DATA_WIDTH-1:0] bias1,
            input wire enable,
            output wire out_valid,
            output wire selected_action_a,
            output wire [DATA_WIDTH-1:0] value_estimate_a,
            output wire selected_action_b,
            output wire [DATA_WIDTH-1:0] value_estimate_b
        );

          wire [(2*DATA_WIDTH):0] score0_a_full;
          wire [(2*DATA_WIDTH):0] score1_a_full;
          wire [(2*DATA_WIDTH):0] score0_b_full;
          wire [(2*DATA_WIDTH):0] score1_b_full;
          wire [DATA_WIDTH-1:0] score0_a;
          wire [DATA_WIDTH-1:0] score1_a;
          wire [DATA_WIDTH-1:0] score0_b;
          wire [DATA_WIDTH-1:0] score1_b;
          wire [DATA_WIDTH:0] value_sum_a;
          wire [DATA_WIDTH:0] value_sum_b;

          assign score0_a_full = (obs0_a * weight0) + bias0;
          assign score1_a_full = (obs1_a * weight1) + bias1;
          assign score0_b_full = (obs0_b * weight0) + bias0;
          assign score1_b_full = (obs1_b * weight1) + bias1;
          assign score0_a = score0_a_full[DATA_WIDTH-1:0];
          assign score1_a = score1_a_full[DATA_WIDTH-1:0];
          assign score0_b = score0_b_full[DATA_WIDTH-1:0];
          assign score1_b = score1_b_full[DATA_WIDTH-1:0];
          assign value_sum_a = {1'b0, score0_a} + {1'b0, score1_a};
          assign value_sum_b = {1'b0, score0_b} + {1'b0, score1_b};
          assign selected_action_a = score1_a > score0_a;
          assign selected_action_b = score1_b > score0_b;
          assign value_estimate_a = value_sum_a[DATA_WIDTH:1];
          assign value_estimate_b = value_sum_b[DATA_WIDTH:1];
          assign out_valid = in_valid && enable;

        endmodule
        """
    )
    dual_td_update_core = dedent(
        """\
        module dual_td_update_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] reward_a,
            input wire [DATA_WIDTH-1:0] next_value_a,
            input wire [DATA_WIDTH-1:0] value_estimate_a,
            input wire [DATA_WIDTH-1:0] reward_b,
            input wire [DATA_WIDTH-1:0] next_value_b,
            input wire [DATA_WIDTH-1:0] value_estimate_b,
            input wire [DATA_WIDTH-1:0] alpha,
            output wire out_valid,
            output wire [DATA_WIDTH-1:0] updated_value_a,
            output wire [DATA_WIDTH-1:0] updated_value_b
        );

          wire [DATA_WIDTH:0] td_error_a_full;
          wire [DATA_WIDTH:0] td_error_b_full;
          wire [(2*DATA_WIDTH)-1:0] update_product_a;
          wire [(2*DATA_WIDTH)-1:0] update_product_b;
          wire [DATA_WIDTH-1:0] update_delta_a;
          wire [DATA_WIDTH-1:0] update_delta_b;

          assign td_error_a_full = {1'b0, reward_a} + {1'b0, next_value_a} - {1'b0, value_estimate_a};
          assign td_error_b_full = {1'b0, reward_b} + {1'b0, next_value_b} - {1'b0, value_estimate_b};
          assign update_product_a = alpha * td_error_a_full[DATA_WIDTH-1:0];
          assign update_product_b = alpha * td_error_b_full[DATA_WIDTH-1:0];
          assign update_delta_a = update_product_a[(2*DATA_WIDTH)-1:4];
          assign update_delta_b = update_product_b[(2*DATA_WIDTH)-1:4];
          assign updated_value_a = value_estimate_a + update_delta_a;
          assign updated_value_b = value_estimate_b + update_delta_b;
          assign out_valid = in_valid;

        endmodule
        """
    )
    batch_result_stage = dedent(
        """\
        module batch_result_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire out_ready,
            input wire selected_action_a,
            input wire [DATA_WIDTH-1:0] value_estimate_a,
            input wire [DATA_WIDTH-1:0] updated_value_a,
            input wire selected_action_b,
            input wire [DATA_WIDTH-1:0] value_estimate_b,
            input wire [DATA_WIDTH-1:0] updated_value_b,
            input wire done_a,
            input wire done_b,
            output reg result_valid,
            input wire result_ready,
            output reg selected_action_a_out,
            output reg [DATA_WIDTH-1:0] value_estimate_a_out,
            output reg [DATA_WIDTH-1:0] updated_value_a_out,
            output reg selected_action_b_out,
            output reg [DATA_WIDTH-1:0] value_estimate_b_out,
            output reg [DATA_WIDTH-1:0] updated_value_b_out,
            output reg batch_done_out,
            output reg irq
        );

          assign out_ready = !result_valid || result_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              result_valid <= 1'b0;
              selected_action_a_out <= 1'b0;
              value_estimate_a_out <= {DATA_WIDTH{1'b0}};
              updated_value_a_out <= {DATA_WIDTH{1'b0}};
              selected_action_b_out <= 1'b0;
              value_estimate_b_out <= {DATA_WIDTH{1'b0}};
              updated_value_b_out <= {DATA_WIDTH{1'b0}};
              batch_done_out <= 1'b0;
              irq <= 1'b0;
            end else begin
              if (result_valid && result_ready) begin
                if (batch_done_out) begin
                  irq <= 1'b1;
                end
                result_valid <= 1'b0;
              end
              if (in_valid && out_ready) begin
                result_valid <= 1'b1;
                selected_action_a_out <= selected_action_a;
                value_estimate_a_out <= value_estimate_a;
                updated_value_a_out <= updated_value_a;
                selected_action_b_out <= selected_action_b;
                value_estimate_b_out <= value_estimate_b;
                updated_value_b_out <= updated_value_b;
                batch_done_out <= done_a | done_b;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/batch_config_bank.v": batch_config_bank,
        "rtl/batch_sample_buffer.v": batch_sample_buffer,
        "rtl/dual_policy_value_core.v": dual_policy_value_core,
        "rtl/dual_td_update_core.v": dual_td_update_core,
        "rtl/batch_result_stage.v": batch_result_stage,
    }


def _batch_config_bank_rtl() -> str:
    return dedent(
        """\
        module batch_config_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [DATA_WIDTH-1:0] cfg_data,
            output reg [DATA_WIDTH-1:0] weight0,
            output reg [DATA_WIDTH-1:0] bias0,
            output reg [DATA_WIDTH-1:0] weight1,
            output reg [DATA_WIDTH-1:0] bias1,
            output reg [DATA_WIDTH-1:0] alpha,
            output reg enable
        );

          assign cfg_ready = 1'b1;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              weight0 <= {DATA_WIDTH{1'b0}};
              bias0 <= {DATA_WIDTH{1'b0}};
              weight1 <= {DATA_WIDTH{1'b0}};
              bias1 <= {DATA_WIDTH{1'b0}};
              alpha <= {DATA_WIDTH{1'b0}};
              enable <= 1'b0;
            end else if (cfg_valid && cfg_ready) begin
              case (cfg_addr)
                3'd0: weight0 <= cfg_data;
                3'd1: bias0 <= cfg_data;
                3'd2: weight1 <= cfg_data;
                3'd3: bias1 <= cfg_data;
                3'd4: alpha <= cfg_data;
                3'd5: enable <= cfg_data[0];
                default: enable <= enable;
              endcase
            end
          end

        endmodule
        """
    )


def _composed_replay_arbiter_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire host_valid,
            output wire host_ready,
            input wire [{msb}:0] host_state,
            input wire host_action,
            input wire [{msb}:0] host_reward,
            input wire [{msb}:0] host_next_state,
            input wire host_done,
            input wire sample_req_valid,
            output wire sample_req_ready,
            input wire [1:0] sample_index,
            output wire sample_valid,
            input wire sample_ready,
            output wire [{msb}:0] sample_state,
            output wire sample_action,
            output wire [{msb}:0] sample_reward,
            output wire [{msb}:0] sample_next_state,
            output wire sample_done,
            output wire [2:0] occupancy,
            output wire [1:0] write_index,
            output wire irq
        );

          wire packet_valid;
          wire packet_ready;
          wire [{msb}:0] packet_state;
          wire packet_action;
          wire [{msb}:0] packet_reward;
          wire [{msb}:0] packet_next_state;
          wire packet_done;
          wire mem_write_valid;
          wire [1:0] mem_write_addr;
          wire [{msb}:0] mem_write_state;
          wire mem_write_action;
          wire [{msb}:0] mem_write_reward;
          wire [{msb}:0] mem_write_next_state;
          wire mem_write_done;
          wire mem_read_valid;
          wire [1:0] mem_read_addr;
          wire write_accepted;
          wire read_valid_out;
          wire [{msb}:0] read_state;
          wire read_action;
          wire [{msb}:0] read_reward;
          wire [{msb}:0] read_next_state;
          wire read_done;
          wire sample_stage_ready;

          host_transition_packetizer #(
            .DATA_WIDTH({width})
          ) u_host_transition_packetizer (
            .host_valid(host_valid),
            .host_ready(host_ready),
            .host_state(host_state),
            .host_action(host_action),
            .host_reward(host_reward),
            .host_next_state(host_next_state),
            .host_done(host_done),
            .packet_ready(packet_ready),
            .packet_valid(packet_valid),
            .packet_state(packet_state),
            .packet_action(packet_action),
            .packet_reward(packet_reward),
            .packet_next_state(packet_next_state),
            .packet_done(packet_done)
          );

          replay_index_allocator u_replay_index_allocator (
            .clk(clk),
            .rst_n(rst_n),
            .write_accepted(write_accepted),
            .write_index(write_index),
            .occupancy(occupancy)
          );

          replay_request_arbiter #(
            .DATA_WIDTH({width})
          ) u_replay_request_arbiter (
            .write_valid(packet_valid),
            .write_ready(packet_ready),
            .write_index(write_index),
            .occupancy(occupancy),
            .write_state(packet_state),
            .write_action(packet_action),
            .write_reward(packet_reward),
            .write_next_state(packet_next_state),
            .write_done(packet_done),
            .read_req_valid(sample_req_valid),
            .sample_index(sample_index),
            .sample_stage_ready(sample_stage_ready),
            .sample_req_ready(sample_req_ready),
            .mem_write_valid(mem_write_valid),
            .mem_write_addr(mem_write_addr),
            .mem_write_state(mem_write_state),
            .mem_write_action(mem_write_action),
            .mem_write_reward(mem_write_reward),
            .mem_write_next_state(mem_write_next_state),
            .mem_write_done(mem_write_done),
            .mem_read_valid(mem_read_valid),
            .mem_read_addr(mem_read_addr),
            .write_accepted(write_accepted)
          );

          replay_memory_bank #(
            .DATA_WIDTH({width})
          ) u_replay_memory_bank (
            .clk(clk),
            .rst_n(rst_n),
            .write_valid(mem_write_valid),
            .write_addr(mem_write_addr),
            .write_state(mem_write_state),
            .write_action(mem_write_action),
            .write_reward(mem_write_reward),
            .write_next_state(mem_write_next_state),
            .write_done(mem_write_done),
            .read_valid(mem_read_valid),
            .read_addr(mem_read_addr),
            .read_valid_out(read_valid_out),
            .read_state(read_state),
            .read_action(read_action),
            .read_reward(read_reward),
            .read_next_state(read_next_state),
            .read_done(read_done)
          );

          sample_packet_stage #(
            .DATA_WIDTH({width})
          ) u_sample_packet_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(read_valid_out),
            .in_ready(sample_stage_ready),
            .sample_state(read_state),
            .sample_action(read_action),
            .sample_reward(read_reward),
            .sample_next_state(read_next_state),
            .sample_done(read_done),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample_state_out(sample_state),
            .sample_action_out(sample_action),
            .sample_reward_out(sample_reward),
            .sample_next_state_out(sample_next_state),
            .sample_done_out(sample_done),
            .irq(irq)
          );

        endmodule
        """
    )
    host_transition_packetizer = dedent(
        """\
        module host_transition_packetizer #(
            parameter DATA_WIDTH = 8
        ) (
            input wire host_valid,
            output wire host_ready,
            input wire [DATA_WIDTH-1:0] host_state,
            input wire host_action,
            input wire [DATA_WIDTH-1:0] host_reward,
            input wire [DATA_WIDTH-1:0] host_next_state,
            input wire host_done,
            input wire packet_ready,
            output wire packet_valid,
            output wire [DATA_WIDTH-1:0] packet_state,
            output wire packet_action,
            output wire [DATA_WIDTH-1:0] packet_reward,
            output wire [DATA_WIDTH-1:0] packet_next_state,
            output wire packet_done
        );

          assign host_ready = packet_ready;
          assign packet_valid = host_valid && packet_ready;
          assign packet_state = host_state;
          assign packet_action = host_action;
          assign packet_reward = host_reward;
          assign packet_next_state = host_next_state;
          assign packet_done = host_done;

        endmodule
        """
    )
    replay_index_allocator = dedent(
        """\
        module replay_index_allocator (
            input wire clk,
            input wire rst_n,
            input wire write_accepted,
            output reg [1:0] write_index,
            output reg [2:0] occupancy
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              write_index <= 2'd0;
              occupancy <= 3'd0;
            end else if (write_accepted) begin
              write_index <= write_index + 2'd1;
              if (occupancy < 3'd4) begin
                occupancy <= occupancy + 3'd1;
              end
            end
          end

        endmodule
        """
    )
    replay_request_arbiter = dedent(
        """\
        module replay_request_arbiter #(
            parameter DATA_WIDTH = 8
        ) (
            input wire write_valid,
            output wire write_ready,
            input wire [1:0] write_index,
            input wire [2:0] occupancy,
            input wire [DATA_WIDTH-1:0] write_state,
            input wire write_action,
            input wire [DATA_WIDTH-1:0] write_reward,
            input wire [DATA_WIDTH-1:0] write_next_state,
            input wire write_done,
            input wire read_req_valid,
            input wire [1:0] sample_index,
            input wire sample_stage_ready,
            output wire sample_req_ready,
            output wire mem_write_valid,
            output wire [1:0] mem_write_addr,
            output wire [DATA_WIDTH-1:0] mem_write_state,
            output wire mem_write_action,
            output wire [DATA_WIDTH-1:0] mem_write_reward,
            output wire [DATA_WIDTH-1:0] mem_write_next_state,
            output wire mem_write_done,
            output wire mem_read_valid,
            output wire [1:0] mem_read_addr,
            output wire write_accepted
        );

          wire read_index_valid;

          assign write_ready = 1'b1;
          assign write_accepted = write_valid && write_ready;
          assign read_index_valid = {1'b0, sample_index} < occupancy;
          assign sample_req_ready = !write_valid && read_index_valid && sample_stage_ready;
          assign mem_write_valid = write_accepted;
          assign mem_write_addr = write_index;
          assign mem_write_state = write_state;
          assign mem_write_action = write_action;
          assign mem_write_reward = write_reward;
          assign mem_write_next_state = write_next_state;
          assign mem_write_done = write_done;
          assign mem_read_valid = read_req_valid && sample_req_ready;
          assign mem_read_addr = sample_index;

        endmodule
        """
    )
    replay_memory_bank = dedent(
        """\
        module replay_memory_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire write_valid,
            input wire [1:0] write_addr,
            input wire [DATA_WIDTH-1:0] write_state,
            input wire write_action,
            input wire [DATA_WIDTH-1:0] write_reward,
            input wire [DATA_WIDTH-1:0] write_next_state,
            input wire write_done,
            input wire read_valid,
            input wire [1:0] read_addr,
            output reg read_valid_out,
            output reg [DATA_WIDTH-1:0] read_state,
            output reg read_action,
            output reg [DATA_WIDTH-1:0] read_reward,
            output reg [DATA_WIDTH-1:0] read_next_state,
            output reg read_done
        );

          reg [DATA_WIDTH-1:0] state_mem [0:3];
          reg action_mem [0:3];
          reg [DATA_WIDTH-1:0] reward_mem [0:3];
          reg [DATA_WIDTH-1:0] next_state_mem [0:3];
          reg done_mem [0:3];

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              read_valid_out <= 1'b0;
              read_state <= {DATA_WIDTH{1'b0}};
              read_action <= 1'b0;
              read_reward <= {DATA_WIDTH{1'b0}};
              read_next_state <= {DATA_WIDTH{1'b0}};
              read_done <= 1'b0;
            end else begin
              read_valid_out <= read_valid;
              if (write_valid) begin
                state_mem[write_addr] <= write_state;
                action_mem[write_addr] <= write_action;
                reward_mem[write_addr] <= write_reward;
                next_state_mem[write_addr] <= write_next_state;
                done_mem[write_addr] <= write_done;
              end
              if (read_valid) begin
                read_state <= state_mem[read_addr];
                read_action <= action_mem[read_addr];
                read_reward <= reward_mem[read_addr];
                read_next_state <= next_state_mem[read_addr];
                read_done <= done_mem[read_addr];
              end
            end
          end

        endmodule
        """
    )
    sample_packet_stage = dedent(
        """\
        module sample_packet_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] sample_state,
            input wire sample_action,
            input wire [DATA_WIDTH-1:0] sample_reward,
            input wire [DATA_WIDTH-1:0] sample_next_state,
            input wire sample_done,
            output reg sample_valid,
            input wire sample_ready,
            output reg [DATA_WIDTH-1:0] sample_state_out,
            output reg sample_action_out,
            output reg [DATA_WIDTH-1:0] sample_reward_out,
            output reg [DATA_WIDTH-1:0] sample_next_state_out,
            output reg sample_done_out,
            output reg irq
        );

          assign in_ready = !sample_valid || sample_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sample_valid <= 1'b0;
              sample_state_out <= {DATA_WIDTH{1'b0}};
              sample_action_out <= 1'b0;
              sample_reward_out <= {DATA_WIDTH{1'b0}};
              sample_next_state_out <= {DATA_WIDTH{1'b0}};
              sample_done_out <= 1'b0;
              irq <= 1'b0;
            end else begin
              if (sample_valid && sample_ready) begin
                irq <= 1'b1;
                sample_valid <= 1'b0;
              end
              if (in_valid && in_ready) begin
                sample_valid <= 1'b1;
                sample_state_out <= sample_state;
                sample_action_out <= sample_action;
                sample_reward_out <= sample_reward;
                sample_next_state_out <= sample_next_state;
                sample_done_out <= sample_done;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/host_transition_packetizer.v": host_transition_packetizer,
        "rtl/replay_index_allocator.v": replay_index_allocator,
        "rtl/replay_request_arbiter.v": replay_request_arbiter,
        "rtl/replay_memory_bank.v": replay_memory_bank,
        "rtl/sample_packet_stage.v": sample_packet_stage,
    }


def _predicted_qor(request: ProjectRequest, platform: PlatformProfile) -> dict[str, object]:
    resource_shape = _resource_shape(request)
    assumptions = {
        "data_width": request.width,
        "task_type": request.task_type,
        "single_clock": True,
        "no_vendor_ip": True,
        "estimate_type": "pre_synthesis_model_prediction",
    }
    if request.task_type == "counter":
        assumptions["counter_width"] = request.width
    return {
        "project_name": request.project_name,
        "target": {
            "platform": platform.name,
            "vendor": platform.vendor,
            "toolchain": platform.toolchain,
        },
        "predicted": {
            "lut": resource_shape["lut"],
            "ff": resource_shape["ff"],
            "bram": resource_shape["bram"],
            "dsp": resource_shape["dsp"],
            "fmax_mhz": min(500.0, platform.clock_hz / 1_000_000 * 3),
            "confidence": 0.65,
        },
        "assumptions": assumptions,
    }


def _default_description(request: ProjectRequest) -> str:
    descriptions = {
        "counter": f"Generate a {request.width}-bit synchronous counter with enable and active-low reset.",
        "fifo": f"Generate a {request.width}-bit synchronous FIFO with depth 4.",
        "simple_fsm": "Generate a simple three-state FSM with start and done handshake.",
        "ram_read_write": f"Generate a {request.width}-bit by 4-entry synchronous RAM read/write block.",
        "uart_tx": "Generate an 8-bit UART transmitter with baud tick generation.",
        "spi_master": "Generate an 8-bit SPI master with clock division and shift engine.",
        "pwm_controller": f"Generate a {request.width}-bit PWM controller with timer and channel modules.",
        "fir_filter": f"Generate a {request.width}-bit three-tap FIR filter with MAC helpers.",
        "streaming_valid_ready": (
            f"Generate a {request.width}-bit valid-ready streaming pipeline with buffering."
        ),
        "matrix_vector_mac": f"Generate a {request.width}-bit fixed matrix-vector dot product engine.",
        "composed_event_counter": (
            f"Generate a {request.width}-bit component-composed event counter using "
            "an event gate and counter core."
        ),
        "composed_stream_accumulator": (
            f"Generate a {request.width}-bit component-composed streaming accumulator "
            "using a skid buffer and accumulator core."
        ),
        "composed_stream_fork": (
            f"Generate a {request.width}-bit component-composed valid-ready stream fork "
            "using a skid buffer, fork, and two registered output stages."
        ),
        "composed_dual_stream_join": (
            f"Generate a {request.width}-bit T4 component-composed dual-stream join "
            "using two skid buffers, a join, an accumulator, and an output stage."
        ),
        "composed_vector_mac_pipeline": (
            f"Generate a {request.width}-bit T5 component-composed vector MAC feature pipeline "
            "using feature and weight skid buffers, a vector MAC core, and an output stage."
        ),
        "composed_td_update_core": (
            f"Generate a {request.width}-bit T6 component-composed TD update datapath "
            "using an input tuple stage, discount core, TD update core, and output stage."
        ),
        "composed_policy_value_shell": (
            f"Generate a {request.width}-bit T7 component-composed policy/value accelerator shell "
            "using config registers, observation capture, policy scoring, action selection, and output staging."
        ),
        "composed_replay_sample_shell": (
            f"Generate a {request.width}-bit T8 component-composed replay sample shell "
            "using host sample staging, a small replay store, sample packing, read staging, and occupancy reporting."
        ),
        "composed_host_protocol_shell": (
            f"Generate a {request.width}-bit T9 component-composed host protocol shell "
            "using AXI-lite-style control/status, AXI-stream-style output, and irq reporting."
        ),
        "composed_rl_accelerator_shell": (
            f"Generate a {request.width}-bit T10 component-composed RL accelerator shell "
            "using host config, sample capture, policy/value scoring, TD update, result streaming, and irq reporting."
        ),
        "composed_batch_rl_accelerator_shell": (
            f"Generate a {request.width}-bit T11 component-composed batch RL accelerator shell "
            "using shared config, two-lane sample capture, dual-lane policy/value and TD update, result staging, and irq reporting."
        ),
        "composed_replay_arbiter_shell": (
            f"Generate a {request.width}-bit T12 component-composed replay arbiter shell "
            "using host transition packetization, indexed sample requests, replay memory arbitration, and irq reporting."
        ),
    }
    return descriptions[request.task_type]


def _interface(request: ProjectRequest, platform: PlatformProfile) -> dict[str, object]:
    common = {
        "clock": "clk",
        "reset": "rst_n",
        "reset_polarity": platform.reset_polarity,
    }
    if request.task_type == "counter":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "en", "width": 1},
                ],
                "outputs": [{"name": "count", "width": request.width}],
            }
        )
    elif request.task_type == "fifo":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "wr_en", "width": 1},
                    {"name": "rd_en", "width": 1},
                    {"name": "din", "width": request.width},
                ],
                "outputs": [
                    {"name": "dout", "width": request.width},
                    {"name": "full", "width": 1},
                    {"name": "empty", "width": 1},
                ],
            }
        )
    elif request.task_type == "simple_fsm":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                ],
                "outputs": [
                    {"name": "done", "width": 1},
                    {"name": "state_value", "width": max(2, request.width)},
                ],
            }
        )
    elif request.task_type == "ram_read_write":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "we", "width": 1},
                    {"name": "addr", "width": 2},
                    {"name": "wdata", "width": request.width},
                ],
                "outputs": [{"name": "rdata", "width": request.width}],
            }
        )
    elif request.task_type == "uart_tx":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                    {"name": "data", "width": 8},
                ],
                "outputs": [
                    {"name": "tx", "width": 1},
                    {"name": "busy", "width": 1},
                    {"name": "done", "width": 1},
                ],
            }
        )
    elif request.task_type == "spi_master":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                    {"name": "tx_data", "width": 8},
                    {"name": "miso", "width": 1},
                ],
                "outputs": [
                    {"name": "rx_data", "width": 8},
                    {"name": "busy", "width": 1},
                    {"name": "done", "width": 1},
                    {"name": "sclk", "width": 1},
                    {"name": "mosi", "width": 1},
                    {"name": "cs_n", "width": 1},
                ],
            }
        )
    elif request.task_type == "pwm_controller":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "duty", "width": request.width},
                ],
                "outputs": [{"name": "pwm_out", "width": 1}],
            }
        )
    elif request.task_type == "fir_filter":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "sample_valid", "width": 1},
                    {"name": "sample", "width": request.width},
                ],
                "outputs": [
                    {"name": "result_valid", "width": 1},
                    {"name": "result", "width": request.width + 3},
                ],
            }
        )
    elif request.task_type == "streaming_valid_ready":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_data", "width": request.width},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "out_data", "width": request.width},
                ],
            }
        )
    elif request.task_type == "matrix_vector_mac":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                ],
                "outputs": [
                    {"name": "busy", "width": 1},
                    {"name": "done", "width": 1},
                    {"name": "result", "width": request.width + 4},
                ],
            }
        )
    elif request.task_type == "composed_event_counter":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "event_valid", "width": 1},
                ],
                "outputs": [{"name": "count", "width": request.width}],
            }
        )
    elif request.task_type == "composed_stream_accumulator":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_data", "width": request.width},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "sample_valid", "width": 1},
                    {"name": "sum", "width": request.width + 4},
                ],
            }
        )
    elif request.task_type == "composed_stream_fork":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_data", "width": request.width},
                    {"name": "out0_ready", "width": 1},
                    {"name": "out1_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out0_valid", "width": 1},
                    {"name": "out0_data", "width": request.width},
                    {"name": "out1_valid", "width": 1},
                    {"name": "out1_data", "width": request.width},
                ],
            }
        )
    elif request.task_type == "composed_dual_stream_join":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in0_valid", "width": 1},
                    {"name": "in0_data", "width": request.width},
                    {"name": "in1_valid", "width": 1},
                    {"name": "in1_data", "width": request.width},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in0_ready", "width": 1},
                    {"name": "in1_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "out_data", "width": request.width + 4},
                ],
            }
        )
    elif request.task_type == "composed_vector_mac_pipeline":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "feature_valid", "width": 1},
                    {"name": "feature_data", "width": request.width},
                    {"name": "weight_valid", "width": 1},
                    {"name": "weight_data", "width": request.width},
                    {"name": "bias", "width": request.width * 2},
                    {"name": "score_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "feature_ready", "width": 1},
                    {"name": "weight_ready", "width": 1},
                    {"name": "score_valid", "width": 1},
                    {"name": "score_data", "width": request.width * 2},
                ],
            }
        )
    elif request.task_type == "composed_td_update_core":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "reward", "width": request.width},
                    {"name": "value", "width": request.width},
                    {"name": "next_value", "width": request.width},
                    {"name": "gamma", "width": request.width},
                    {"name": "alpha", "width": request.width},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "td_error", "width": request.width},
                    {"name": "updated_value", "width": request.width},
                ],
            }
        )
    elif request.task_type == "composed_policy_value_shell":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "cfg_valid", "width": 1},
                    {"name": "cfg_addr", "width": 3},
                    {"name": "cfg_data", "width": request.width},
                    {"name": "obs_valid", "width": 1},
                    {"name": "obs0", "width": request.width},
                    {"name": "obs1", "width": request.width},
                    {"name": "action_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "cfg_ready", "width": 1},
                    {"name": "obs_ready", "width": 1},
                    {"name": "action_valid", "width": 1},
                    {"name": "selected_action", "width": 1},
                    {"name": "value_estimate", "width": request.width},
                ],
            }
        )
    elif request.task_type == "composed_replay_sample_shell":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "host_valid", "width": 1},
                    {"name": "host_state", "width": request.width},
                    {"name": "host_action", "width": 1},
                    {"name": "host_reward", "width": request.width},
                    {"name": "host_next_state", "width": request.width},
                    {"name": "host_done", "width": 1},
                    {"name": "sample_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "host_ready", "width": 1},
                    {"name": "sample_valid", "width": 1},
                    {"name": "sample_state", "width": request.width},
                    {"name": "sample_action", "width": 1},
                    {"name": "sample_reward", "width": request.width},
                    {"name": "sample_next_state", "width": request.width},
                    {"name": "sample_done", "width": 1},
                    {"name": "occupancy", "width": 3},
                ],
            }
        )
    elif request.task_type == "composed_host_protocol_shell":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "s_axi_awvalid", "width": 1},
                    {"name": "s_axi_awaddr", "width": 4},
                    {"name": "s_axi_wvalid", "width": 1},
                    {"name": "s_axi_wdata", "width": request.width},
                    {"name": "s_axi_wstrb", "width": 1},
                    {"name": "s_axi_bready", "width": 1},
                    {"name": "s_axi_arvalid", "width": 1},
                    {"name": "s_axi_araddr", "width": 4},
                    {"name": "s_axi_rready", "width": 1},
                    {"name": "m_axis_tready", "width": 1},
                ],
                "outputs": [
                    {"name": "s_axi_awready", "width": 1},
                    {"name": "s_axi_wready", "width": 1},
                    {"name": "s_axi_bvalid", "width": 1},
                    {"name": "s_axi_arready", "width": 1},
                    {"name": "s_axi_rvalid", "width": 1},
                    {"name": "s_axi_rdata", "width": request.width},
                    {"name": "m_axis_tvalid", "width": 1},
                    {"name": "m_axis_tdata", "width": request.width * 2},
                    {"name": "m_axis_tlast", "width": 1},
                    {"name": "irq", "width": 1},
                ],
            }
        )
    elif request.task_type == "composed_rl_accelerator_shell":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "cfg_valid", "width": 1},
                    {"name": "cfg_addr", "width": 3},
                    {"name": "cfg_data", "width": request.width},
                    {"name": "sample_valid", "width": 1},
                    {"name": "obs0", "width": request.width},
                    {"name": "obs1", "width": request.width},
                    {"name": "reward", "width": request.width},
                    {"name": "next_value", "width": request.width},
                    {"name": "done_in", "width": 1},
                    {"name": "result_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "cfg_ready", "width": 1},
                    {"name": "sample_ready", "width": 1},
                    {"name": "result_valid", "width": 1},
                    {"name": "selected_action", "width": 1},
                    {"name": "value_estimate", "width": request.width},
                    {"name": "updated_value", "width": request.width},
                    {"name": "episode_done", "width": 1},
                    {"name": "irq", "width": 1},
                ],
            }
        )
    elif request.task_type == "composed_batch_rl_accelerator_shell":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "cfg_valid", "width": 1},
                    {"name": "cfg_addr", "width": 3},
                    {"name": "cfg_data", "width": request.width},
                    {"name": "batch_valid", "width": 1},
                    {"name": "obs0_a", "width": request.width},
                    {"name": "obs1_a", "width": request.width},
                    {"name": "reward_a", "width": request.width},
                    {"name": "next_value_a", "width": request.width},
                    {"name": "done_a", "width": 1},
                    {"name": "obs0_b", "width": request.width},
                    {"name": "obs1_b", "width": request.width},
                    {"name": "reward_b", "width": request.width},
                    {"name": "next_value_b", "width": request.width},
                    {"name": "done_b", "width": 1},
                    {"name": "result_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "cfg_ready", "width": 1},
                    {"name": "batch_ready", "width": 1},
                    {"name": "result_valid", "width": 1},
                    {"name": "selected_action_a", "width": 1},
                    {"name": "value_estimate_a", "width": request.width},
                    {"name": "updated_value_a", "width": request.width},
                    {"name": "selected_action_b", "width": 1},
                    {"name": "value_estimate_b", "width": request.width},
                    {"name": "updated_value_b", "width": request.width},
                    {"name": "batch_done", "width": 1},
                    {"name": "irq", "width": 1},
                ],
            }
        )
    elif request.task_type == "composed_replay_arbiter_shell":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "host_valid", "width": 1},
                    {"name": "host_state", "width": request.width},
                    {"name": "host_action", "width": 1},
                    {"name": "host_reward", "width": request.width},
                    {"name": "host_next_state", "width": request.width},
                    {"name": "host_done", "width": 1},
                    {"name": "sample_req_valid", "width": 1},
                    {"name": "sample_index", "width": 2},
                    {"name": "sample_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "host_ready", "width": 1},
                    {"name": "sample_req_ready", "width": 1},
                    {"name": "sample_valid", "width": 1},
                    {"name": "sample_state", "width": request.width},
                    {"name": "sample_action", "width": 1},
                    {"name": "sample_reward", "width": request.width},
                    {"name": "sample_next_state", "width": request.width},
                    {"name": "sample_done", "width": 1},
                    {"name": "occupancy", "width": 3},
                    {"name": "write_index", "width": 2},
                    {"name": "irq", "width": 1},
                ],
            }
        )
    return common


def _expected_behavior(request: ProjectRequest) -> str:
    expectations = {
        "counter": "count increments when en is high and holds when en is low",
        "fifo": "data written into the FIFO is read back in order",
        "simple_fsm": "FSM transitions from idle to run to done and back to idle",
        "ram_read_write": "data written to an address can be read back from the same address",
        "uart_tx": "start launches an 8-bit LSB-first UART frame with start and stop bits",
        "spi_master": "start launches an 8-bit MSB-first SPI transfer and captures MISO data",
        "pwm_controller": "pwm_out is high when the free-running counter is below duty",
        "fir_filter": "valid input samples produce a three-tap [1, 2, 1] FIR result",
        "streaming_valid_ready": "valid-ready transfers preserve data order across stalls",
        "matrix_vector_mac": "start computes the fixed four-element dot product and pulses done",
        "composed_event_counter": "event_valid pulses pass through an event gate and increment the counter core",
        "composed_stream_accumulator": (
            "valid input samples pass through a skid buffer and accumulate into the running sum"
        ),
        "composed_stream_fork": (
            "valid input samples pass through a skid buffer and are duplicated to two output stages"
        ),
        "composed_dual_stream_join": (
            "two valid-ready input streams are buffered, synchronized, joined, accumulated, and staged"
        ),
        "composed_vector_mac_pipeline": (
            "paired feature and weight streams are buffered, multiplied and accumulated over a fixed vector length, "
            "biased, and staged as score output"
        ),
        "composed_td_update_core": (
            "a reward, value, next value, discount factor, and learning rate tuple is staged, "
            "converted into a temporal-difference error, and used to emit an updated value"
        ),
        "composed_policy_value_shell": (
            "configuration writes set weights, biases, and enable; observations are scored, compared, "
            "and staged as selected action plus value estimate"
        ),
        "composed_replay_sample_shell": (
            "host-side transition samples are staged into a small replay store, then read back in FIFO order "
            "through a fabric-side valid-ready sample output with occupancy reporting"
        ),
        "composed_host_protocol_shell": (
            "AXI-lite-style writes configure sample registers and start streaming; one AXI-stream-style payload "
            "is emitted, status can be read back, and irq remains asserted until cleared"
        ),
        "composed_rl_accelerator_shell": (
            "configuration writes set weights, biases, alpha, and enable; sample tuples are captured, "
            "scored into selected action and value estimate, updated through a TD datapath, "
            "and staged as result output with episode irq reporting"
        ),
        "composed_batch_rl_accelerator_shell": (
            "configuration writes set shared weights, biases, alpha, and enable; a two-lane batch is captured, "
            "each lane is scored and updated through duplicated policy/value and TD datapaths, "
            "and both lane results are staged with batch_done irq reporting"
        ),
        "composed_replay_arbiter_shell": (
            "host transition packets are written into a depth-4 replay memory, indexed sample requests are "
            "gated by occupancy and arbitrated behind host writes, and accepted read packets are staged with irq reporting"
        ),
    }
    return expectations[request.task_type]


def _test_pass_means(request: ProjectRequest) -> str:
    return f"Self-checking testbench prints TEST_PASS only when {_expected_behavior(request)}."


def _resource_shape(request: ProjectRequest) -> dict[str, int]:
    if request.task_type == "counter":
        return {"lut": max(1, request.width // 2), "ff": request.width, "bram": 0, "dsp": 0}
    if request.task_type == "fifo":
        return {"lut": max(4, request.width), "ff": request.width * 4 + 8, "bram": 0, "dsp": 0}
    if request.task_type == "simple_fsm":
        return {"lut": 6, "ff": max(2, request.width) + 3, "bram": 0, "dsp": 0}
    if request.task_type == "ram_read_write":
        return {"lut": max(4, request.width), "ff": request.width * 4 + request.width, "bram": 0, "dsp": 0}
    if request.task_type == "uart_tx":
        return {"lut": max(12, request.width * 2), "ff": request.width + 16, "bram": 0, "dsp": 0}
    if request.task_type == "spi_master":
        return {"lut": max(16, request.width * 2), "ff": request.width * 2 + 16, "bram": 0, "dsp": 0}
    if request.task_type == "pwm_controller":
        return {"lut": max(8, request.width), "ff": request.width * 2, "bram": 0, "dsp": 0}
    if request.task_type == "fir_filter":
        return {"lut": max(20, request.width * 3), "ff": request.width * 3, "bram": 0, "dsp": 2}
    if request.task_type == "streaming_valid_ready":
        return {"lut": max(10, request.width), "ff": request.width * 2 + 4, "bram": 0, "dsp": 0}
    if request.task_type == "matrix_vector_mac":
        return {"lut": max(24, request.width * 4), "ff": request.width * 4, "bram": 0, "dsp": 2}
    if request.task_type == "composed_event_counter":
        return {"lut": max(4, request.width // 2 + 2), "ff": request.width, "bram": 0, "dsp": 0}
    if request.task_type == "composed_stream_accumulator":
        return {"lut": max(16, request.width * 2), "ff": request.width * 3 + 8, "bram": 0, "dsp": 0}
    if request.task_type == "composed_stream_fork":
        return {"lut": max(18, request.width * 2 + 6), "ff": request.width * 3 + 6, "bram": 0, "dsp": 0}
    if request.task_type == "composed_dual_stream_join":
        return {"lut": max(32, request.width * 4 + 12), "ff": request.width * 5 + 18, "bram": 0, "dsp": 0}
    if request.task_type == "composed_vector_mac_pipeline":
        return {"lut": max(48, request.width * 6 + 20), "ff": request.width * 6 + 24, "bram": 0, "dsp": 1}
    if request.task_type == "composed_td_update_core":
        return {"lut": max(56, request.width * 7 + 24), "ff": request.width * 7 + 28, "bram": 0, "dsp": 1}
    if request.task_type == "composed_policy_value_shell":
        return {"lut": max(72, request.width * 9 + 32), "ff": request.width * 8 + 40, "bram": 0, "dsp": 2}
    if request.task_type == "composed_replay_sample_shell":
        return {"lut": max(88, request.width * 10 + 44), "ff": request.width * 12 + 64, "bram": 0, "dsp": 0}
    if request.task_type == "composed_host_protocol_shell":
        return {"lut": max(104, request.width * 12 + 64), "ff": request.width * 10 + 72, "bram": 0, "dsp": 0}
    if request.task_type == "composed_rl_accelerator_shell":
        return {"lut": max(136, request.width * 16 + 80), "ff": request.width * 14 + 96, "bram": 0, "dsp": 2}
    if request.task_type == "composed_batch_rl_accelerator_shell":
        return {"lut": max(184, request.width * 24 + 112), "ff": request.width * 24 + 144, "bram": 0, "dsp": 4}
    if request.task_type == "composed_replay_arbiter_shell":
        return {"lut": max(160, request.width * 18 + 120), "ff": request.width * 18 + 128, "bram": 0, "dsp": 0}
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
