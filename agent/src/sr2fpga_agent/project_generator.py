"""Deterministic V1 project generator for small RTL tasks."""

from __future__ import annotations

import json
import re
from textwrap import dedent

from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.task_catalog import task_family_spec_for_family_id
from sr2fpga_agent.task_families import (
    SUPPORTED_TASK_TYPES,
    TASK_TYPE_ALIASES,
    family_id_for_task_type,
)
from sr2fpga_agent.task_families.basic import (
    counter_rtl as _counter_rtl,
    counter_testbench as _counter_testbench,
    ram_read_write_rtl as _ram_read_write_rtl,
    ram_read_write_testbench as _ram_read_write_testbench,
    simple_fsm_rtl as _simple_fsm_rtl,
    simple_fsm_testbench as _simple_fsm_testbench,
)
from sr2fpga_agent.task_families.datapath import (
    alu_control_unit_rtl_files as _alu_control_unit_rtl_files,
    alu_control_unit_testbench as _alu_control_unit_testbench,
    composed_vector_mac_pipeline_rtl_files as _composed_vector_mac_pipeline_rtl_files,
    composed_vector_mac_pipeline_testbench as _composed_vector_mac_pipeline_testbench,
    crc_stream_checker_rtl_files as _crc_stream_checker_rtl_files,
    crc_stream_checker_testbench as _crc_stream_checker_testbench,
    fir_filter_rtl_files as _fir_filter_rtl_files,
    fir_filter_testbench as _fir_filter_testbench,
    matched_filter_rtl_files as _matched_filter_rtl_files,
    matched_filter_testbench as _matched_filter_testbench,
    peak_detector_rtl_files as _peak_detector_rtl_files,
    peak_detector_testbench as _peak_detector_testbench,
    pulse_radar_signal_rtl_files as _pulse_radar_signal_rtl_files,
    pulse_radar_signal_testbench as _pulse_radar_signal_testbench,
    matrix_vector_mac_rtl_files as _matrix_vector_mac_rtl_files,
    matrix_vector_mac_testbench as _matrix_vector_mac_testbench,
    pwm_controller_rtl_files as _pwm_controller_rtl_files,
    pwm_controller_testbench as _pwm_controller_testbench,
)
from sr2fpga_agent.task_families.image import (
    sobel_threshold_rtl_files as _sobel_threshold_rtl_files,
    sobel_threshold_testbench as _sobel_threshold_testbench,
    vision_defect_core_rtl_files as _vision_defect_core_rtl_files,
    vision_defect_core_testbench as _vision_defect_core_testbench,
)
from sr2fpga_agent.task_families.protocol import (
    fifo_rtl as _fifo_rtl,
    fifo_testbench as _fifo_testbench,
    spi_master_rtl_files as _spi_master_rtl_files,
    spi_master_testbench as _spi_master_testbench,
    uart_fifo_loopback_rtl_files as _uart_fifo_loopback_rtl_files,
    uart_fifo_loopback_testbench as _uart_fifo_loopback_testbench,
    uart_rx_rtl_files as _uart_rx_rtl_files,
    uart_rx_testbench as _uart_rx_testbench,
    uart_tx_rtl_files as _uart_tx_rtl_files,
    uart_tx_testbench as _uart_tx_testbench,
)
from sr2fpga_agent.task_families.rl import (
    batch_config_bank_rtl as _batch_config_bank_rtl,
    composed_batch_rl_accelerator_shell_rtl_files as _composed_batch_rl_accelerator_shell_rtl_files,
    composed_batch_rl_accelerator_shell_testbench as _composed_batch_rl_accelerator_shell_testbench,
    composed_host_protocol_shell_rtl_files as _composed_host_protocol_shell_rtl_files,
    composed_host_protocol_shell_testbench as _composed_host_protocol_shell_testbench,
    composed_policy_value_shell_rtl_files as _composed_policy_value_shell_rtl_files,
    composed_policy_value_shell_testbench as _composed_policy_value_shell_testbench,
    composed_replay_arbiter_shell_rtl_files as _composed_replay_arbiter_shell_rtl_files,
    composed_replay_arbiter_shell_testbench as _composed_replay_arbiter_shell_testbench,
    composed_replay_sample_shell_rtl_files as _composed_replay_sample_shell_rtl_files,
    composed_replay_sample_shell_testbench as _composed_replay_sample_shell_testbench,
    composed_rl_accelerator_shell_rtl_files as _composed_rl_accelerator_shell_rtl_files,
    composed_rl_accelerator_shell_testbench as _composed_rl_accelerator_shell_testbench,
    composed_td_update_core_rtl_files as _composed_td_update_core_rtl_files,
    composed_td_update_core_testbench as _composed_td_update_core_testbench,
)
from sr2fpga_agent.task_families.stream import (
    composed_dual_stream_join_rtl_files as _composed_dual_stream_join_rtl_files,
    composed_dual_stream_join_testbench as _composed_dual_stream_join_testbench,
    composed_event_counter_rtl_files as _composed_event_counter_rtl_files,
    composed_event_counter_testbench as _composed_event_counter_testbench,
    composed_stream_fork_rtl_files as _composed_stream_fork_rtl_files,
    composed_stream_fork_testbench as _composed_stream_fork_testbench,
    composed_stream_accumulator_rtl_files as _composed_stream_accumulator_rtl_files,
    composed_stream_accumulator_testbench as _composed_stream_accumulator_testbench,
    pattern_matcher_rtl_files as _pattern_matcher_rtl_files,
    pattern_matcher_testbench as _pattern_matcher_testbench,
    streaming_valid_ready_rtl_files as _streaming_valid_ready_rtl_files,
    streaming_valid_ready_testbench as _streaming_valid_ready_testbench,
    stream_trigger_filter_rtl_files as _stream_trigger_filter_rtl_files,
)

COMPONENT_LIBRARY_ID = "sr2fpga_deterministic_components_v1"
TOPOLOGY_EDGE_DATA_FLOW_TASK_TYPES = {"composed_td_update_core"}

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
        "difficulty_tier": "T1",
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
            {"from": "top.accum_ready", "to": "skid_buffer.out_ready"},
            {"from": "top.accum_ready", "to": "accumulator_core.sample_ready"},
            {"from": "accumulator_core.sum", "to": "top.sum"},
        ],
    },
    "composed_stream_fork": {
        "topology_id": "t3_stream_fork",
        "difficulty_tier": "T2",
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
        "difficulty_tier": "T2",
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
            {"from": "stream_stage.in_ready", "to": "stream_join.out_ready"},
            {"from": "accumulator_core.sample_valid", "to": "stream_stage.in_valid"},
            {"from": "accumulator_core.sum", "to": "stream_stage.in_data"},
            {"from": "stream_stage.in_ready", "to": "accumulator_core.sample_ready"},
            {"from": "top.out_ready", "to": "stream_stage.out_ready"},
            {"from": "stream_stage.out_valid", "to": "top.out_valid"},
            {"from": "stream_stage.out_data", "to": "top.out_data"},
        ],
    },
    "composed_vector_mac_pipeline": {
        "topology_id": "t5_vector_mac_pipeline",
        "difficulty_tier": "T3",
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
        "difficulty_tier": "T3",
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
        "difficulty_tier": "T3",
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
        "difficulty_tier": "T3",
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
        "difficulty_tier": "T4",
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
        "difficulty_tier": "T4",
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
        "difficulty_tier": "T4",
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
        "difficulty_tier": "T4",
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
        request = _canonical_request(request)

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


def _canonical_request(request: ProjectRequest) -> ProjectRequest:
    canonical_task_type = TASK_TYPE_ALIASES.get(request.task_type, request.task_type)
    if canonical_task_type == request.task_type:
        return request
    return ProjectRequest(
        task_type=canonical_task_type,
        width=request.width,
        project_name=request.project_name,
        description=request.description,
    )


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
    top_parameters = _top_parameters(request)
    components = _v12_components(modules)
    instances = _v12_instances(
        rtl_files,
        components,
        top_module,
        clock_name=str(interface["clock"]),
        reset_name=str(interface["reset"]),
    )
    instances = _v12_task_specific_instances(
        request,
        instances,
        components,
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
            "parameters": top_parameters,
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
            "scenarios": _verification_scenarios(request),
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


def _v12_task_specific_instances(
    request: ProjectRequest,
    instances: list[dict[str, object]],
    components: list[dict[str, object]],
    *,
    clock_name: str,
    reset_name: str,
) -> list[dict[str, object]]:
    canonical_instances = {
        "vision_defect_core": (
            ("u_sobel_window", "sobel_window"),
            ("u_sobel_threshold_core", "sobel_threshold_core"),
            ("u_vision_defect_accumulator", "vision_defect_accumulator"),
            ("u_vision_io_control", "vision_io_control"),
        ),
        "pattern_matcher": (("u_pattern_matcher", "pattern_matcher"),),
        "stream_trigger_filter": (
            ("u_pattern_matcher", "pattern_matcher"),
            ("u_trigger_fsm", "trigger_fsm"),
            ("u_stream_packer", "stream_packer"),
        ),
    }.get(request.task_type, ())
    if not canonical_instances:
        return instances

    components_by_name = {str(component["name"]): component for component in components}
    by_name = {str(instance["name"]): instance for instance in instances}
    for instance_name, component_name in canonical_instances:
        by_name[instance_name] = {
            "name": instance_name,
            "component": component_name,
            "parameter_values": _v12_component_parameter_values(components_by_name[component_name]),
            "clock": clock_name,
            "reset": reset_name,
            "owns_state": [],
        }
    return list(by_name.values())


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
    elif request.task_type == "alu_control_unit":
        flag_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "status_flags"),
            owner,
        )
        registers.extend(
            [
                {"name": "result", "owner": flag_owner, "width": request.width},
                {"name": "result_valid", "owner": flag_owner, "width": 1},
                {"name": "zero", "owner": flag_owner, "width": 1},
                {"name": "carry", "owner": flag_owner, "width": 1},
                {"name": "negative", "owner": flag_owner, "width": 1},
            ]
        )
    elif request.task_type == "crc_stream_checker":
        accumulator_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "stream_frame_accumulator"),
            owner,
        )
        status_owner = next(
            (str(instance["name"]) for instance in instances if instance.get("component") == "crc_status"),
            owner,
        )
        registers.extend(
            [
                {"name": "crc_state", "owner": accumulator_owner, "width": 8},
                {"name": "frame_crc", "owner": accumulator_owner, "width": 8},
                {"name": "frame_done", "owner": accumulator_owner, "width": 1},
                {"name": "out_valid", "owner": status_owner, "width": 1},
                {"name": "crc_value", "owner": status_owner, "width": 8},
                {"name": "crc_match", "owner": status_owner, "width": 1},
            ]
        )
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
    if request.task_type == "pulse_radar_signal":
        return _pulse_radar_data_flow(request)
    if request.task_type == "vision_defect_core":
        return _vision_defect_data_flow()
    if request.task_type in {"pattern_matcher", "stream_trigger_filter"}:
        return _pattern_trigger_data_flow(request)
    topology_flows = _v12_topology_edge_data_flow(request, instances)
    if topology_flows:
        return topology_flows
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


def _pulse_radar_data_flow(request: ProjectRequest) -> list[dict[str, object]]:
    acc_width = request.width * 2 + 2
    edges = [
        ("top.in_valid", "u_matched_filter_core.in_valid", 1),
        ("top.in_sample", "u_matched_filter_core.in_sample", request.width),
        ("top.in_last", "u_matched_filter_core.in_last", 1),
        ("u_matched_filter_core.in_ready", "top.in_ready", 1),
        ("u_matched_filter_core.out_valid", "u_threshold_comparator.in_valid", 1),
        ("u_matched_filter_core.out_correlation", "u_threshold_comparator.in_sample", acc_width),
        ("u_matched_filter_core.out_last", "u_threshold_comparator.in_last", 1),
        ("u_threshold_comparator.in_ready", "u_matched_filter_core.out_ready", 1),
        ("u_threshold_comparator.out_valid", "u_peak_detector_core.in_valid", 1),
        ("u_threshold_comparator.out_sample", "u_peak_detector_core.in_sample", acc_width),
        ("u_threshold_comparator.out_last", "u_peak_detector_core.in_last", 1),
        ("u_peak_detector_core.in_ready", "u_threshold_comparator.out_ready", 1),
        ("u_peak_detector_core.out_valid", "top.out_valid", 1),
        ("top.out_ready", "u_peak_detector_core.out_ready", 1),
        ("u_peak_detector_core.out_peak_found", "top.peak_found", 1),
        ("u_peak_detector_core.out_peak_value", "top.peak_value", acc_width),
        ("u_peak_detector_core.out_peak_index", "top.peak_index", acc_width),
    ]
    return [
        {
            "name": f"pulse_radar_signal_edge_{index:02d}",
            "path": [source, sink],
            "payload": {"name": source.rsplit(".", 1)[-1], "width": width},
            "protocol": "valid_ready" if "valid" in source or "ready" in source or "valid" in sink or "ready" in sink else "wire",
        }
        for index, (source, sink, width) in enumerate(edges)
    ]


def _vision_defect_data_flow() -> list[dict[str, object]]:
    edges = [
        ("top.in_pixel", "u_sobel_window.in_pixel", 8),
        ("u_sobel_window.gx", "u_sobel_threshold_core.gx", 11),
        ("u_sobel_window.gy", "u_sobel_threshold_core.gy", 11),
        ("top.out_edge", "u_vision_defect_accumulator.pixel_edge", 1),
        ("u_vision_defect_accumulator.defect_present", "u_vision_io_control.defect_present", 1),
        ("u_vision_defect_accumulator.first_defect_x", "u_vision_io_control.first_defect_x", 16),
        ("u_vision_defect_accumulator.first_defect_y", "u_vision_io_control.first_defect_y", 16),
        ("u_vision_defect_accumulator.defect_present", "top.defect_present", 1),
        ("u_vision_defect_accumulator.first_defect_x", "top.first_defect_x", 16),
        ("u_vision_defect_accumulator.first_defect_y", "top.first_defect_y", 16),
        ("u_vision_io_control.reported_defect_present", "top.defect_present", 1),
        ("u_vision_io_control.reported_first_defect_x", "top.first_defect_x", 16),
        ("u_vision_io_control.reported_first_defect_y", "top.first_defect_y", 16),
    ]
    return [
        {
            "name": f"vision_defect_core_edge_{index:02d}",
            "path": [source, sink],
            "payload": {"name": source.rsplit(".", 1)[-1], "width": width},
            "protocol": "wire",
        }
        for index, (source, sink, width) in enumerate(edges)
    ]


def _pattern_trigger_data_flow(request: ProjectRequest) -> list[dict[str, object]]:
    if request.task_type == "pattern_matcher":
        edges = [
            ("top.in_data", "u_pattern_matcher.in_data", request.width),
            ("u_pattern_matcher.match_index", "top.out_match_index", 32),
            ("u_pattern_matcher.match_word", "top.out_match_word", request.width * 4),
        ]
    else:
        edges = [
            ("top.in_data", "u_pattern_matcher.in_data", request.width),
            ("u_pattern_matcher.match_index", "u_trigger_fsm.match_index", 32),
            ("u_pattern_matcher.match_word", "u_trigger_fsm.match_word", request.width * 4),
            ("u_trigger_fsm.trigger_index", "u_stream_packer.event_index", 32),
            ("u_trigger_fsm.trigger_word", "u_stream_packer.event_word", request.width * 4),
            ("u_stream_packer.out_match_index", "top.out_match_index", 32),
            ("u_stream_packer.out_match_word", "top.out_match_word", request.width * 4),
        ]
    return [
        {
            "name": f"{request.task_type}_edge_{index:02d}",
            "path": [source, sink],
            "payload": {"name": source.rsplit(".", 1)[-1], "width": width},
            "protocol": "valid_ready" if "match" in source or "trigger" in source or "event" in source else "wire",
        }
        for index, (source, sink, width) in enumerate(edges)
    ]
def _v12_topology_edge_data_flow(
    request: ProjectRequest,
    instances: list[dict[str, object]],
) -> list[dict[str, object]]:
    topology = COMPONENT_TOPOLOGIES.get(request.task_type)
    if not topology or request.task_type not in TOPOLOGY_EDGE_DATA_FLOW_TASK_TYPES:
        return []
    component_to_instances: dict[str, list[str]] = {}
    for instance in instances:
        component_name = str(instance.get("component", "")).strip()
        instance_name = str(instance.get("name", "")).strip()
        if component_name and instance_name:
            component_to_instances.setdefault(component_name, []).append(instance_name)

    flows: list[dict[str, object]] = []
    for index, edge in enumerate(topology.get("edges", [])):
        source = _v12_resolve_topology_endpoint(str(edge.get("from", "")), component_to_instances)
        sink = _v12_resolve_topology_endpoint(str(edge.get("to", "")), component_to_instances)
        if not source or not sink:
            return []
        source_port = source.rsplit(".", 1)[-1]
        sink_port = sink.rsplit(".", 1)[-1]
        protocol = "valid_ready" if any("valid" in name or "ready" in name for name in (source_port, sink_port)) else "wire"
        flow: dict[str, object] = {
            "name": f"{request.task_type}_edge_{index:02d}_{source_port}_to_{sink_port}",
            "path": [source, sink],
            "payload": {"name": source_port, "width": request.width},
            "protocol": protocol,
        }
        if protocol == "valid_ready":
            flow["timing"] = {
                "latency_cycles": 0,
                "initiation_interval": 1,
                "throughput": "combinational handshake connection",
            }
        flows.append(flow)
    return flows


def _v12_resolve_topology_endpoint(endpoint: str, component_to_instances: dict[str, list[str]]) -> str:
    if "." not in endpoint:
        return ""
    owner, port = endpoint.split(".", 1)
    if owner == "top":
        return endpoint
    instance_names = component_to_instances.get(owner, [])
    if len(instance_names) != 1:
        return ""
    return f"{instance_names[0]}.{port}"


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
    if request.task_type == "vision_defect_core":
        return rules + [
            {
                "name": "accepted_input_to_window",
                "kind": "handshake_rule",
                "condition": "top.in_valid && top.in_ready",
                "effects": [
                    "u_sobel_window.accept receives the pixel and row-major state only after the accepted input handshake"
                ],
                "related_state": [],
                "related_flows": ["vision_defect_core_edge_00"],
            },
            {
                "name": "registered_output_accept",
                "kind": "handshake_rule",
                "condition": "top.out_valid && top.out_ready",
                "effects": [
                    "u_vision_defect_accumulator consumes zero-border-policy registered top.out_edge and top.out_last; u_vision_io_control captures the completed frame report"
                ],
                "related_state": [],
                "related_flows": [
                    "vision_defect_core_edge_03",
                    "vision_defect_core_edge_07",
                    "vision_defect_core_edge_08",
                    "vision_defect_core_edge_09",
                ],
            },
            {
                "name": "out_last_report_select",
                "kind": "enable_rule",
                "condition": "top.out_valid && top.out_last",
                "effects": [
                    "top defect report fields select accumulator current values rather than vision_io_control stored values"
                ],
                "related_state": [],
                "related_flows": [
                    "vision_defect_core_edge_07",
                    "vision_defect_core_edge_08",
                    "vision_defect_core_edge_09",
                ],
            },
            {
                "name": "registered_output_stall",
                "kind": "stall_rule",
                "condition": "top.out_valid && !top.out_ready",
                "effects": ["hold registered top.out_edge, top.out_last, and the selected frame report fields"],
                "related_state": [],
                "related_flows": ["vision_defect_core_edge_03"],
            },
        ]
    if request.task_type in {"pattern_matcher", "stream_trigger_filter"}:
        flow_names = [str(flow["name"]) for flow in data_flow]
        return rules + [
            {
                "name": "accepted_token_window_advance",
                "kind": "handshake_rule",
                "condition": "top.in_valid && top.in_ready",
                "effects": ["advance the four-token shift window and accepted-token index only after an input handshake"],
                "related_state": [],
                "related_flows": flow_names,
            },
            {
                "name": "match_output_stall",
                "kind": "stall_rule",
                "condition": "top.out_valid && !top.out_ready",
                "effects": ["hold match index and matched four-token word stable until the output handshake"],
                "related_state": [],
                "related_flows": flow_names,
            },
        ]
    if request.task_type in {
        "streaming_valid_ready",
        "crc_stream_checker",
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


def _top_parameters(request: ProjectRequest) -> list[dict[str, object]]:
    if request.task_type in {"sobel_threshold", "vision_defect_core"}:
        return [
            {"name": "IMAGE_WIDTH", "default": 5},
            {"name": "IMAGE_HEIGHT", "default": 5},
            {"name": "THRESHOLD", "default": 100},
        ]
    if request.task_type in {"pattern_matcher", "stream_trigger_filter"}:
        return [
            {"name": "TOKEN0", "default": "8'h11"},
            {"name": "TOKEN1", "default": "8'h22"},
            {"name": "TOKEN2", "default": "8'h33"},
            {"name": "TOKEN3", "default": "8'h11"},
        ]
    return []


def _verification_scenarios(request: ProjectRequest) -> list[str]:
    if request.task_type == "sobel_threshold":
        return [
            "reset",
            "flat_image",
            "axis_sensitive_edges",
            "threshold_boundary",
            "border_policy",
            "stall_stability",
            "frame_boundary",
            "missing_final_in_last",
            "reset_during_frame",
        ]
    if request.task_type == "vision_defect_core":
        return [
            "reset",
            "flat_image",
            "threshold_boundary",
            "border_policy",
            "first_defect_coordinate",
            "defect_present_absent",
            "stall_stability",
            "frame_boundary",
            "continuous_frames",
            "reset_during_frame",
        ]
    if request.task_type in {"pattern_matcher", "stream_trigger_filter"}:
        return [
            "reset",
            "no_match",
            "partial_match",
            "exact_match",
            "overlapping_match",
            "back_to_back_matches",
            "boundary_match_index",
            "input_stall",
            "stall_stability",
            "reset_during_partial_match",
            "no_false_positive",
        ]
    return ["reset", "nominal_operation"]


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
    family_spec = task_family_spec_for_family_id(family_id_for_task_type(request.task_type))
    submodules = {
        "counter": [],
        "fifo": [],
        "simple_fsm": [],
        "ram_read_write": [],
        "uart_tx": ["baud_tick_gen", "uart_tx_core"],
        "uart_rx": ["uart_rx_core"],
        "uart_fifo_loopback": ["uart_rx_core", "sync_fifo_core", "uart_tx_core"],
        "spi_master": ["clock_divider", "spi_master_core"],
        "pwm_controller": ["pwm_timer", "pwm_channel"],
        "fir_filter": ["mac_unit", "fir_filter_core"],
        "matched_filter": ["matched_filter_mac", "matched_filter_core"],
        "peak_detector": ["peak_detector_core"],
        "pulse_radar_signal": ["matched_filter_mac", "matched_filter_core", "threshold_comparator", "peak_detector_core"],
        "sobel_threshold": ["sobel_line_buffer", "sobel_window", "sobel_threshold_core"],
        "vision_defect_core": ["sobel_line_buffer", "sobel_window", "sobel_threshold_core", "vision_defect_accumulator", "vision_io_control"],
        "pattern_matcher": ["pattern_matcher"],
        "stream_trigger_filter": ["pattern_matcher", "trigger_fsm", "stream_packer"],
        "streaming_valid_ready": ["skid_buffer", "stream_stage"],
        "matrix_vector_mac": ["vector_rom", "mac_unit", "dot_product_engine"],
        "alu_control_unit": ["control_decode", "alu_core", "status_flags"],
        "crc_stream_checker": ["stream_frame_accumulator", "crc8_update", "crc_status"],
    }
    if request.task_type in COMPONENT_TOPOLOGIES:
        submodules[request.task_type] = list(COMPONENT_TOPOLOGIES[request.task_type]["submodules"])
    architecture = {
        "style": "multi_module" if submodules[request.task_type] else "single_module",
        "top_module": "top",
        "submodules": submodules[request.task_type],
        "task_family_id": family_spec.family_id,
        "difficulty_tier": family_spec.sr2fpga_tier,
        "system_his_profile": family_spec.system_his_profile,
        "skeleton_level": family_spec.skeleton_level,
        "oracle_kind": list(family_spec.oracle_kind),
    }
    if request.task_type in COMPONENT_TOPOLOGIES:
        topology = COMPONENT_TOPOLOGIES[request.task_type]
        architecture.update(
            {
                "generator": "component_topology",
                "topology_id": topology["topology_id"],
                "difficulty_tier": family_spec.sr2fpga_tier,
                "component_library": COMPONENT_LIBRARY_ID,
                "topology": {
                    "nodes": topology["nodes"],
                    "edges": topology["edges"],
                },
            }
        )
    if request.task_type == "sobel_threshold":
        architecture["obligations"] = [
            "two_line_buffer_window",
            "row_major_zero_border",
            "signed_sobel_magnitude",
            "edge_axis_semantics",
            "in_last_gated_frame_flush",
            "one_entry_output_stall_stability",
        ]
    if request.task_type == "vision_defect_core":
        architecture["obligations"] = [
            "two_line_buffer_window",
            "row_major_zero_border",
            "signed_sobel_magnitude",
            "bounded_first_defect_coordinate",
            "in_last_gated_frame_flush",
            "one_entry_output_stall_stability",
        ]
    if request.task_type in {"pattern_matcher", "stream_trigger_filter"}:
        architecture["obligations"] = [
            "four_token_shift_window",
            "accepted_token_match_index",
            "overlapping_match",
            "one_entry_output_backpressure",
            "match_index_packet",
        ]
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
    if request.task_type == "uart_rx":
        return _uart_rx_rtl_files(request.width)
    if request.task_type == "uart_fifo_loopback":
        return _uart_fifo_loopback_rtl_files(request.width)
    if request.task_type == "spi_master":
        return _spi_master_rtl_files(request.width)
    if request.task_type == "pwm_controller":
        return _pwm_controller_rtl_files(request.width)
    if request.task_type == "fir_filter":
        return _fir_filter_rtl_files(request.width)
    if request.task_type == "matched_filter":
        return _matched_filter_rtl_files(request.width)
    if request.task_type == "peak_detector":
        return _peak_detector_rtl_files(request.width)
    if request.task_type == "pulse_radar_signal":
        return _pulse_radar_signal_rtl_files(request.width)
    if request.task_type == "sobel_threshold":
        return _sobel_threshold_rtl_files(request.width)
    if request.task_type == "vision_defect_core":
        return _vision_defect_core_rtl_files(request.width)
    if request.task_type == "pattern_matcher":
        return _pattern_matcher_rtl_files(request.width)
    if request.task_type == "stream_trigger_filter":
        return _stream_trigger_filter_rtl_files(request.width)
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_rtl_files(request.width)
    if request.task_type == "matrix_vector_mac":
        return _matrix_vector_mac_rtl_files(request.width)
    if request.task_type == "alu_control_unit":
        return _alu_control_unit_rtl_files(request.width)
    if request.task_type == "crc_stream_checker":
        return _crc_stream_checker_rtl_files(request.width)
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
        testbench = _counter_testbench(request.width)
    elif request.task_type == "fifo":
        testbench = _fifo_testbench(request.width)
    elif request.task_type == "simple_fsm":
        testbench = _simple_fsm_testbench(max(2, request.width))
    elif request.task_type == "ram_read_write":
        testbench = _ram_read_write_testbench(request.width)
    elif request.task_type == "uart_tx":
        testbench = _uart_tx_testbench()
    elif request.task_type == "uart_rx":
        testbench = _uart_rx_testbench()
    elif request.task_type == "uart_fifo_loopback":
        testbench = _uart_fifo_loopback_testbench()
    elif request.task_type == "spi_master":
        testbench = _spi_master_testbench()
    elif request.task_type == "pwm_controller":
        testbench = _pwm_controller_testbench(request.width)
    elif request.task_type == "fir_filter":
        testbench = _fir_filter_testbench(request.width)
    elif request.task_type == "matched_filter":
        testbench = _matched_filter_testbench(request.width)
    elif request.task_type == "peak_detector":
        testbench = _peak_detector_testbench(request.width)
    elif request.task_type == "pulse_radar_signal":
        testbench = _pulse_radar_signal_testbench(request.width)
    elif request.task_type == "sobel_threshold":
        testbench = _sobel_threshold_testbench()
    elif request.task_type == "vision_defect_core":
        testbench = _vision_defect_core_testbench()
    elif request.task_type == "pattern_matcher":
        testbench = _pattern_matcher_testbench(request.width)
    elif request.task_type == "stream_trigger_filter":
        testbench = _pattern_matcher_testbench(request.width, project_mode=True)
    elif request.task_type == "streaming_valid_ready":
        testbench = _streaming_valid_ready_testbench(request.width)
    elif request.task_type == "matrix_vector_mac":
        testbench = _matrix_vector_mac_testbench(request.width)
    elif request.task_type == "alu_control_unit":
        testbench = _alu_control_unit_testbench(request.width)
    elif request.task_type == "crc_stream_checker":
        testbench = _crc_stream_checker_testbench(request.width)
    elif request.task_type == "composed_event_counter":
        testbench = _composed_event_counter_testbench(request.width)
    elif request.task_type == "composed_stream_accumulator":
        testbench = _composed_stream_accumulator_testbench(request.width)
    elif request.task_type == "composed_stream_fork":
        testbench = _composed_stream_fork_testbench(request.width)
    elif request.task_type == "composed_dual_stream_join":
        testbench = _composed_dual_stream_join_testbench(request.width)
    elif request.task_type == "composed_vector_mac_pipeline":
        testbench = _composed_vector_mac_pipeline_testbench(request.width)
    elif request.task_type == "composed_td_update_core":
        testbench = _composed_td_update_core_testbench(request.width)
    elif request.task_type == "composed_policy_value_shell":
        testbench = _composed_policy_value_shell_testbench(request.width)
    elif request.task_type == "composed_replay_sample_shell":
        testbench = _composed_replay_sample_shell_testbench(request.width)
    elif request.task_type == "composed_host_protocol_shell":
        testbench = _composed_host_protocol_shell_testbench(request.width)
    elif request.task_type == "composed_rl_accelerator_shell":
        testbench = _composed_rl_accelerator_shell_testbench(request.width)
    elif request.task_type == "composed_batch_rl_accelerator_shell":
        testbench = _composed_batch_rl_accelerator_shell_testbench(request.width)
    elif request.task_type == "composed_replay_arbiter_shell":
        testbench = _composed_replay_arbiter_shell_testbench(request.width)
    else:
        raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
    return _with_testbench_timeout(testbench)


def _with_testbench_timeout(testbench: str, timeout_ns: int = 100_000) -> str:
    if "TEST_FAIL timeout" in testbench:
        return testbench
    watchdog = (
        "\n"
        "  initial begin\n"
        f"    #{timeout_ns};\n"
        '    $display("TEST_FAIL timeout waiting for expected input/output behavior");\n'
        "    $finish;\n"
        "  end\n"
    )
    endmodule = "\nendmodule\n"
    if endmodule not in testbench:
        return testbench
    return testbench.replace(endmodule, f"{watchdog}{endmodule}", 1)


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
        "uart_rx": "Generate an 8-bit UART receiver with midpoint start, data, and stop-bit sampling.",
        "uart_fifo_loopback": "Generate an 8-bit UART RX to depth-four FIFO to UART TX loopback.",
        "spi_master": "Generate an 8-bit SPI master with clock division and shift engine.",
        "pwm_controller": f"Generate a {request.width}-bit PWM controller with timer and channel modules.",
        "fir_filter": (
            f"Generate a signed {request.width}-bit valid-ready three-tap FIR filter with [3, -2, 1] "
            "coefficients and MAC helpers."
        ),
        "matched_filter": (
            f"Generate a signed {request.width}-bit valid-ready four-tap matched filter with explicit "
            "correlation accumulation and a one-entry output buffer."
        ),
        "peak_detector": (
            f"Generate a signed {request.width}-bit valid-ready frame peak detector with threshold, "
            "first-index tie breaking, and a one-entry output buffer."
        ),
        "pulse_radar_signal": (
            f"Generate a signed {request.width}-bit pulse-radar stream that correlates samples, applies "
            "a bounded signed threshold clamp, and detects the first maximum per aligned frame."
        ),
        "sobel_threshold": (
            "Generate a row-major 8-bit Sobel threshold stream with a real two-line-buffer 3x3 window, "
            "zero-valued one-pixel borders, and buffered edge-axis metadata."
        ),
        "vision_defect_core": (
            "Generate a bounded row-major 8-bit Sobel defect stream that emits every thresholded edge pixel "
            "and reports one frame-level defect-present flag plus the first thresholded pixel coordinate."
        ),
        "pattern_matcher": (
            "each exact four-token sequence emits the accepted-token index of its ending token and the matched word; "
            "overlaps remain detectable and the one-entry output holds under backpressure"
        ),
        "stream_trigger_filter": (
            "each exact four-token sequence is packetized through trigger_fsm and stream_packer with its accepted-token index "
            "and matched word stable under valid-ready backpressure"
        ),
        "streaming_valid_ready": (
            f"Generate a {request.width}-bit valid-ready streaming pipeline with buffering."
        ),
        "matrix_vector_mac": (
            f"Generate a signed {request.width}-bit valid-ready four-element matrix-vector dot product engine "
            "with fixed [2, -1, 3, 1] coefficients."
        ),
        "alu_control_unit": (
            f"Generate a {request.width}-bit ALU control unit with opcode decode, arithmetic/logic core, "
            "registered result, and zero/carry/negative status flags."
        ),
        "crc_stream_checker": (
            f"Generate a {request.width}-bit valid-ready streaming CRC checker with frame start/end markers, "
            "CRC-8 update logic, and registered match status."
        ),
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
            f"Generate a {request.width}-bit T2 component-composed dual-stream join "
            "using two skid buffers, a join, an accumulator, and an output stage."
        ),
        "composed_vector_mac_pipeline": (
            f"Generate a {request.width}-bit T3 component-composed vector MAC feature pipeline "
            "using feature and weight skid buffers, a vector MAC core, and an output stage."
        ),
        "composed_td_update_core": (
            f"Generate a {request.width}-bit T3 component-composed TD update datapath "
            "using an input tuple stage, discount core, TD update core, and output stage."
        ),
        "composed_policy_value_shell": (
            f"Generate a {request.width}-bit T3 component-composed policy/value accelerator shell "
            "using config registers, observation capture, policy scoring, action selection, and output staging."
        ),
        "composed_replay_sample_shell": (
            f"Generate a {request.width}-bit T3 component-composed replay sample shell "
            "using host sample staging, a small replay store, sample packing, read staging, and occupancy reporting."
        ),
        "composed_host_protocol_shell": (
            f"Generate a {request.width}-bit T4 component-composed host protocol shell "
            "using AXI-lite-style control/status, AXI-stream-style output, and irq reporting."
        ),
        "composed_rl_accelerator_shell": (
            f"Generate a {request.width}-bit T4 component-composed RL accelerator shell "
            "using host config, sample capture, policy/value scoring, TD update, result streaming, and irq reporting."
        ),
        "composed_batch_rl_accelerator_shell": (
            f"Generate a {request.width}-bit T4 component-composed batch RL accelerator shell "
            "using shared config, two-lane sample capture, dual-lane policy/value and TD update, result staging, and irq reporting."
        ),
        "composed_replay_arbiter_shell": (
            f"Generate a {request.width}-bit T4 component-composed replay arbiter shell "
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
    elif request.task_type == "uart_rx":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "rx", "width": 1},
                ],
                "outputs": [
                    {"name": "data", "width": 8},
                    {"name": "data_valid", "width": 1},
                    {"name": "framing_error", "width": 1},
                ],
            }
        )
    elif request.task_type == "uart_fifo_loopback":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "rx", "width": 1},
                    {"name": "tx_enable", "width": 1},
                ],
                "outputs": [{"name": "tx", "width": 1}],
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
                    {"name": "result_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "sample_ready", "width": 1},
                    {"name": "result_valid", "width": 1},
                    {"name": "result", "width": request.width + 3},
                ],
            }
        )
    elif request.task_type == "matched_filter":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_sample", "width": request.width},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "correlation", "width": request.width * 2 + 2},
                ],
            }
        )
    elif request.task_type == "peak_detector":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_sample", "width": request.width},
                    {"name": "in_last", "width": 1},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "peak_found", "width": 1},
                    {"name": "peak_value", "width": request.width},
                    {"name": "peak_index", "width": request.width},
                ],
            }
        )
    elif request.task_type == "pulse_radar_signal":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_sample", "width": request.width},
                    {"name": "in_last", "width": 1},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "peak_found", "width": 1},
                    {"name": "peak_value", "width": request.width * 2 + 2},
                    {"name": "peak_index", "width": request.width * 2 + 2},
                ],
            }
        )
    elif request.task_type == "sobel_threshold":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_pixel", "width": 8},
                    {"name": "in_last", "width": 1},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "out_edge", "width": 1},
                    {"name": "edge_axis", "width": 1},
                    {"name": "out_last", "width": 1},
                ],
            }
        )
    elif request.task_type == "vision_defect_core":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_pixel", "width": 8},
                    {"name": "in_last", "width": 1},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "out_edge", "width": 1},
                    {"name": "out_last", "width": 1},
                    {"name": "defect_present", "width": 1},
                    {"name": "first_defect_x", "width": 16},
                    {"name": "first_defect_y", "width": 16},
                ],
            }
        )
    elif request.task_type in {"pattern_matcher", "stream_trigger_filter"}:
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
                    {"name": "out_match_index", "width": 32},
                    {"name": "out_match_word", "width": request.width * 4},
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
                    {"name": "sample_valid", "width": 1},
                    {"name": "sample", "width": request.width},
                    {"name": "result_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "sample_ready", "width": 1},
                    {"name": "result_valid", "width": 1},
                    {"name": "result", "width": request.width + 4},
                ],
            }
        )
    elif request.task_type == "alu_control_unit":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "valid", "width": 1},
                    {"name": "op", "width": 3},
                    {"name": "lhs", "width": request.width},
                    {"name": "rhs", "width": request.width},
                ],
                "outputs": [
                    {"name": "ready", "width": 1},
                    {"name": "result_valid", "width": 1},
                    {"name": "result", "width": request.width},
                    {"name": "zero", "width": 1},
                    {"name": "carry", "width": 1},
                    {"name": "negative", "width": 1},
                ],
            }
        )
    elif request.task_type == "crc_stream_checker":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_data", "width": request.width},
                    {"name": "frame_start", "width": 1},
                    {"name": "frame_end", "width": 1},
                    {"name": "expected_crc", "width": 8},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "crc_value", "width": 8},
                    {"name": "crc_match", "width": 1},
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
                    {"name": "accum_ready", "width": 1},
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
        "uart_rx": "midpoint sampling decodes an 8-bit LSB-first UART frame and reports framing errors",
        "uart_fifo_loopback": "received UART bytes are buffered in order and transmitted without drops or duplicates",
        "spi_master": "start launches an 8-bit MSB-first SPI transfer and captures MISO data",
        "pwm_controller": "pwm_out is high when the free-running counter is below duty",
        "fir_filter": (
            "signed valid-ready input samples produce a three-tap [3, -2, 1] FIR result, and the output "
            "remains stable under backpressure"
        ),
        "matched_filter": (
            "signed valid-ready input samples are correlated against the four-tap [-1, 2, -3, 4] template, "
            "and the one-entry correlation output remains stable under backpressure"
        ),
        "peak_detector": (
            "signed valid-ready samples are reduced per in_last frame to the first maximum at or above threshold, "
            "with a defined empty result and a one-entry backpressure-safe output"
        ),
        "pulse_radar_signal": (
            "accepted in_last markers remain aligned with matched-filter correlations through backpressure, "
            "and each completed correlation frame reports its first threshold-qualified maximum"
        ),
        "sobel_threshold": (
            "each accepted 5x5 row-major 8-bit frame emits exactly 25 row-major threshold bits with zero borders; "
            "the final input must assert in_last before bottom-border flush and out_last; edge_axis is one only when "
            "abs(Gx) is at least abs(Gy), and all output fields remain stable under stall"
        ),
        "vision_defect_core": (
            "each accepted 5x5 row-major 8-bit frame emits exactly 25 thresholded edge bits with zero borders; "
            "the out_last beat reports whether any thresholded edge occurred and the first such row-major coordinate, "
            "or zero coordinates when no defect is present, while all output fields remain stable under stall"
        ),
        "pattern_matcher": (
            "each exact four-token sequence emits the accepted-token index of its ending token and the matched word; "
            "overlaps remain detectable and the one-entry output holds under backpressure"
        ),
        "stream_trigger_filter": (
            "each exact four-token sequence is packetized through trigger_fsm and stream_packer with its accepted-token index "
            "and matched word stable under valid-ready backpressure"
        ),
        "streaming_valid_ready": "valid-ready transfers preserve data order across stalls",
        "matrix_vector_mac": (
            "four signed valid-ready input samples are multiplied by fixed [2, -1, 3, 1] coefficients, "
            "accumulated without truncation, and emitted as one backpressure-safe result"
        ),
        "alu_control_unit": (
            "valid op/lhs/rhs inputs are decoded, executed by the ALU core, and captured with zero, carry, "
            "and negative flags"
        ),
        "crc_stream_checker": (
            "valid-ready input bytes are accumulated across a marked frame, updated through CRC-8 logic, "
            "and reported with expected CRC match status"
        ),
        "composed_event_counter": "event_valid pulses pass through an event gate and increment the counter core",
        "composed_stream_accumulator": (
            "valid input samples remain stable under accumulator backpressure, pass through a skid buffer, "
            "and accumulate into the running sum when accepted"
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
    if request.task_type == "uart_rx":
        return {"lut": max(14, request.width * 2), "ff": request.width + 22, "bram": 0, "dsp": 0}
    if request.task_type == "uart_fifo_loopback":
        return {"lut": max(28, request.width * 4), "ff": request.width * 5 + 36, "bram": 0, "dsp": 0}
    if request.task_type == "spi_master":
        return {"lut": max(16, request.width * 2), "ff": request.width * 2 + 16, "bram": 0, "dsp": 0}
    if request.task_type == "pwm_controller":
        return {"lut": max(8, request.width), "ff": request.width * 2, "bram": 0, "dsp": 0}
    if request.task_type == "fir_filter":
        return {"lut": max(20, request.width * 3), "ff": request.width * 3, "bram": 0, "dsp": 2}
    if request.task_type == "matched_filter":
        return {"lut": max(28, request.width * 4), "ff": request.width * 8 + 4, "bram": 0, "dsp": 4}
    if request.task_type == "peak_detector":
        return {"lut": max(16, request.width * 2), "ff": request.width * 4 + 3, "bram": 0, "dsp": 0}
    if request.task_type == "pulse_radar_signal":
        return {"lut": max(48, request.width * 6), "ff": request.width * 12 + 8, "bram": 0, "dsp": 4}
    if request.task_type == "sobel_threshold":
        return {"lut": 96, "ff": 80, "bram": 0, "dsp": 0}
    if request.task_type == "vision_defect_core":
        return {"lut": 124, "ff": 146, "bram": 0, "dsp": 0}
    if request.task_type == "pattern_matcher":
        return {"lut": max(24, request.width * 3), "ff": request.width * 7 + 36, "bram": 0, "dsp": 0}
    if request.task_type == "stream_trigger_filter":
        return {"lut": max(36, request.width * 5), "ff": request.width * 15 + 108, "bram": 0, "dsp": 0}
    if request.task_type == "streaming_valid_ready":
        return {"lut": max(10, request.width), "ff": request.width * 2 + 4, "bram": 0, "dsp": 0}
    if request.task_type == "matrix_vector_mac":
        return {"lut": max(24, request.width * 4), "ff": request.width * 4, "bram": 0, "dsp": 2}
    if request.task_type == "alu_control_unit":
        return {"lut": max(20, request.width * 3 + 8), "ff": request.width + 4, "bram": 0, "dsp": 0}
    if request.task_type == "crc_stream_checker":
        return {"lut": max(28, request.width * 4 + 12), "ff": request.width + 20, "bram": 0, "dsp": 0}
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
