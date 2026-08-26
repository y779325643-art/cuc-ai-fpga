"""Synthetic failure injectors for SR2FPGA repair trajectory generation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.task_catalog import task_family_spec_for_family_id
from sr2fpga_agent.task_families import family_id_for_task_type


@dataclass(frozen=True)
class FailureInjectingProjectGenerator:
    """Wrap a project generator and apply named synthetic failures."""

    base_generator: object
    injectors: list[str]

    @property
    def his_source_used_for_generation(self) -> object:
        return getattr(self.base_generator, "his_source_used_for_generation", "generated")

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        project = self.base_generator.generate(request, platform)
        return apply_failure_injectors(project, self.injectors)


def apply_failure_injectors(project: GeneratedProject, injectors: list[str]) -> GeneratedProject:
    files = dict(project.files)
    for injector in injectors:
        if injector == "rename_reset_port":
            files = _rename_reset_port(files)
        elif injector == "undefined_signal_reference":
            files = _undefined_signal_reference(files)
        elif injector == "missing_manifest_source":
            files = _missing_manifest_source(files)
        elif injector == "wrong_top_module":
            files = _wrong_top_module(files)
        elif injector == "width_mismatch":
            files = _width_mismatch(files)
        elif injector == "testbench_expected_value_mismatch":
            files = _testbench_expected_value_mismatch(files)
        elif injector == "constraint_missing_clock":
            files = _constraint_missing_clock(files)
        elif injector == "multimodule_connection_mismatch":
            files = _multimodule_connection_mismatch(files)
        else:
            raise ValueError(f"Unsupported failure injector: {injector}")
    return GeneratedProject(project_name=project.project_name, files=files)


def oracle_mutation_projects(project: GeneratedProject, task_type: str) -> dict[str, GeneratedProject | None]:
    """Create catalog-declared DUT-only mutants and expose unsupported cases."""
    family = _task_family_spec_for_project(project, task_type)
    if family is None:
        return {}
    mutations: dict[str, GeneratedProject | None] = {}
    for mutation_name in family.mutation_suite:
        files = _oracle_dut_mutation(project.files, family.family_id, mutation_name)
        mutations[mutation_name] = (
            None if files is None else GeneratedProject(project_name=project.project_name, files=files)
        )
    return mutations


def _task_family_spec_for_project(project: GeneratedProject, task_type: str):
    requested_family = _task_family_spec(task_type)
    if requested_family is None:
        return None
    system_his = project.files.get("system_his.json")
    if system_his is not None:
        try:
            declared_task_type = json.loads(system_his).get("task_type")
        except (json.JSONDecodeError, AttributeError):
            return None
        if not isinstance(declared_task_type, str):
            return None
        declared_family = _task_family_spec(declared_task_type)
        if declared_family is None or declared_family.family_id != requested_family.family_id:
            return None
        return declared_family
    return requested_family


def _task_family_spec(task_type: str):
    try:
        return task_family_spec_for_family_id(family_id_for_task_type(task_type))
    except KeyError:
        try:
            return task_family_spec_for_family_id(task_type)
        except KeyError:
            return None


def _oracle_dut_mutation(
    files: dict[str, str],
    family_id: str,
    mutation_name: str,
) -> dict[str, str] | None:
    if family_id == "single_dual_port_ram" and mutation_name == "async_read_in_sync_bram_family":
        source = files.get("rtl/top.v")
        if source is None:
            return None
        source, output_count = re.subn(
            r"output reg (\[[^\]]+\]) rdata",
            r"output wire \1 rdata",
            source,
            count=1,
        )
        source, reset_count = re.subn(r"^\s*rdata <= \d+'d0;\r?\n", "", source, count=1, flags=re.MULTILINE)
        source, read_count = re.subn(r"^\s*rdata <= mem\[addr\];\r?\n", "", source, count=1, flags=re.MULTILINE)
        source, assign_count = re.subn(
            r"(\s+integer i;\r?\n)",
            r"\1\n  assign rdata = mem[addr];\n",
            source,
            count=1,
        )
        if (output_count, reset_count, read_count, assign_count) != (1, 1, 1, 1):
            return None
        updated = dict(files)
        updated["rtl/top.v"] = source
        return updated

    replacements = {
        ("single_dual_port_ram", "wrong_read_during_write"): (
            "rtl/top.v",
            (("rdata <= mem[addr];", "rdata <= we ? wdata : mem[addr];"),),
        ),
        ("single_dual_port_ram", "wrong_address_width"): (
            "rtl/top.v",
            (("mem[addr]", "mem[{1'b0, addr[0]}]"),),
        ),
        ("valid_ready_stream_accumulator", "payload_changes_under_stall"): (
            "rtl/skid_buffer.v",
            ((
                """    end else if (in_ready) begin
      valid_r <= in_valid;
      if (in_valid) begin
        data_r <= in_data;
      end
    end""",
                """    end else if (in_ready) begin
      valid_r <= in_valid;
      if (in_valid) begin
        data_r <= in_data;
      end
    end else if (valid_r && !out_ready) begin
      data_r <= data_r + {{(WIDTH-1){1'b0}}, 1'b1};
    end""",
            ),),
        ),
        ("valid_ready_stream_accumulator", "valid_drops_under_stall"): (
            "rtl/skid_buffer.v",
            ((
                """    end else if (in_ready) begin
      valid_r <= in_valid;
      if (in_valid) begin
        data_r <= in_data;
      end
    end""",
                """    end else if (in_ready) begin
      valid_r <= in_valid;
      if (in_valid) begin
        data_r <= in_data;
      end
    end else if (valid_r && !out_ready) begin
      valid_r <= 1'b0;
    end""",
            ),),
        ),
        ("valid_ready_stream_accumulator", "drop_transaction"): (
            "rtl/accumulator_core.v",
            ((
                "end else if (sample_valid && sample_ready) begin",
                "end else if (sample_valid && sample_ready && sample[0]) begin",
            ),),
        ),
        ("valid_ready_stream_accumulator", "wrong_accumulation"): (
            "rtl/accumulator_core.v",
            (("sum <= sum +", "sum <= sum -"),),
        ),
        ("stream_fork_join", "drop_one_branch"): (
            "rtl/stream_join.v",
            ((
                "assign out_data = in0_data + in1_data;",
                "assign out_data = in0_data + {WIDTH{^in1_data}};",
            ),),
        ),
        ("stream_fork_join", "duplicate_transaction"): (
            "rtl/stream_join.v",
            ((
                "assign out_data = in0_data + in1_data;",
                "assign out_data = in0_data + in0_data + {WIDTH{^in1_data}};",
            ),),
        ),
        ("stream_fork_join", "wrong_join_order"): (
            "rtl/stream_join.v",
            (("assign out_data = in0_data + in1_data;", "assign out_data = in0_data - in1_data;"),),
        ),
        ("stream_fork_join", "missing_backpressure"): (
            "rtl/stream_join.v",
            (
                (
                    "assign in0_ready = out_ready && in1_valid;",
                    "assign in0_ready = in1_valid && (out_ready || in0_data[0]);",
                ),
                (
                    "assign in1_ready = out_ready && in0_valid;",
                    "assign in1_ready = in0_valid && (out_ready || in1_data[0]);",
                ),
            ),
        ),
        ("mac_array", "remove_signed_cast"): (
            "rtl/vector_mac_core.v",
            (("$signed(feature_data) * $signed(weight_data)", "feature_data * weight_data"),),
        ),
        ("mac_array", "truncate_accumulator"): (
            "rtl/vector_mac_core.v",
            ((
                "assign next_accumulator = $signed(accumulator) + product;",
                "assign next_accumulator = ($signed(accumulator) + product) & "
                "{{(SCORE_WIDTH-DATA_WIDTH){1'b0}}, {DATA_WIDTH{1'b1}}};",
            ),),
        ),
        ("mac_array", "wrong_latency"): (
            "rtl/vector_mac_core.v",
            (("localparam [1:0] LAST_INDEX = 2'd3;", "localparam [1:0] LAST_INDEX = 2'd2;"),),
        ),
        ("mac_array", "wrong_operand_order"): (
            "rtl/vector_mac_core.v",
            ((
                "$signed(weight_data)",
                "$signed({weight_data[DATA_WIDTH-2:0], weight_data[DATA_WIDTH-1]})",
            ),),
        ),
        ("sync_fifo", "remove_full_guard"): ("rtl/top.v", (("wr_en && !full", "wr_en"),)),
        ("sync_fifo", "remove_empty_guard"): ("rtl/top.v", (("rd_en && !empty", "rd_en"),)),
        ("sync_fifo", "wrong_pointer_update"): (
            "rtl/top.v",
            (("rd_ptr <= rd_ptr + 2'd1;", "rd_ptr <= rd_ptr;"),),
        ),
        ("sync_fifo", "same_cycle_push_pop_bug"): (
            "rtl/top.v",
            (("default: count <= count;", "default: count <= count + 3'd1;"),),
        ),
        ("valid_ready_stream_stage", "valid_drops_under_stall"): (
            "rtl/stream_stage.v",
            ((
                "end else if (in_ready) begin",
                "end else if (!out_ready) begin\n      out_valid <= 1'b0;\n    end else if (in_ready) begin",
            ),),
        ),
        ("valid_ready_stream_stage", "payload_changes_under_stall"): (
            "rtl/stream_stage.v",
            ((
                "end else if (in_ready) begin",
                "end else if (!out_ready && out_valid) begin\n"
                "      out_data <= out_data + {{(WIDTH-1){1'b0}}, 1'b1};\n"
                "    end else if (in_ready) begin",
            ),),
        ),
        ("valid_ready_stream_stage", "drop_transaction"): (
            "rtl/stream_stage.v",
            (("out_valid <= in_valid;", "out_valid <= 1'b0;"),),
        ),
        ("fir_filter", "wrong_coeff_order"): (
            "rtl/fir_filter_core.v",
            (
                ("COEFF_NEW = 3'sd3;", "COEFF_NEW = 3'sd1;"),
                ("COEFF_OLD = 3'sd1;", "COEFF_OLD = 3'sd3;"),
            ),
        ),
        ("fir_filter", "truncate_accumulator"): (
            "rtl/fir_filter_core.v",
            ((
                "result <= filtered_result;",
                "result <= {{(RESULT_WIDTH-WIDTH){filtered_result[WIDTH-1]}}, filtered_result[WIDTH-1:0]};",
            ),),
        ),
        ("fir_filter", "remove_signed_cast"): (
            "rtl/mac_unit.v",
            ((
                "$signed(sample) * $signed(coefficient)",
                "sample * coefficient",
            ),),
        ),
        ("fir_filter", "missing_stall"): (
            "rtl/fir_filter_core.v",
            (("end else if (sample_ready) begin", "end else begin"),),
        ),
        ("fir_filter", "off_by_one_latency"): (
            "rtl/fir_filter_core.v",
            (
                (
                    "reg signed [WIDTH-1:0] sample_d1;",
                    "reg signed [WIDTH-1:0] sample_d1;\n  reg delayed_valid;",
                ),
                (
                    "result_valid <= 1'b0;\n      result <= {RESULT_WIDTH{1'b0}};",
                    "result_valid <= 1'b0;\n      delayed_valid <= 1'b0;\n      result <= {RESULT_WIDTH{1'b0}};",
                ),
                (
                    "result_valid <= sample_valid;",
                    "result_valid <= delayed_valid;\n      delayed_valid <= sample_valid;",
                ),
            ),
        ),
        ("matched_filter", "reversed_template"): (
            "rtl/matched_filter_core.v",
            (
                ("parameter TAP0 = -1,", "parameter TAP0 = 4,"),
                ("parameter TAP3 = 4", "parameter TAP3 = -1"),
            ),
        ),
        ("matched_filter", "truncate_correlation"): (
            "rtl/matched_filter_core.v",
            ((
                "out_correlation <= correlation_sum;",
                "out_correlation <= {{(ACC_WIDTH-WIDTH){correlation_sum[WIDTH-1]}}, correlation_sum[WIDTH-1:0]};",
            ),),
        ),
        ("matched_filter", "wrong_latency"): (
            "rtl/matched_filter_core.v",
            (
                (
                    "reg signed [ACC_WIDTH-1:0] sample_d2;",
                    "reg signed [ACC_WIDTH-1:0] sample_d2;\n  reg delayed_valid;",
                ),
                (
                    "out_valid <= 1'b0;\n      out_correlation",
                    "out_valid <= 1'b0;\n      delayed_valid <= 1'b0;\n      out_correlation",
                ),
                (
                    "out_valid <= in_valid;",
                    "out_valid <= delayed_valid;\n      delayed_valid <= in_valid;",
                ),
            ),
        ),
        ("matched_filter", "missing_stall"): (
            "rtl/matched_filter_core.v",
            (("end else if (in_ready) begin", "end else begin"),),
        ),
        ("peak_detector", "wrong_threshold"): (
            "rtl/peak_detector_core.v",
            (("$signed(in_sample) >= THRESHOLD", "$signed(in_sample) > THRESHOLD"),),
        ),
        ("peak_detector", "off_by_one_peak"): (
            "rtl/peak_detector_core.v",
            ((
                "out_peak_value <= candidate_found ? (candidate_is_new_peak ? candidate_value : peak_value) : {WIDTH{1'b0}};",
                "out_peak_value <= candidate_found ? peak_value : {WIDTH{1'b0}};",
            ),),
        ),
        ("peak_detector", "wrong_tie_break"): (
            "rtl/peak_detector_core.v",
            (("candidate_value > peak_value", "candidate_value >= peak_value"),),
        ),
        ("p_pulse_radar_signal", "reversed_template"): (
            "rtl/matched_filter_core.v",
            (
                ("parameter TAP0 = -1,", "parameter TAP0 = 4,"),
                ("parameter TAP3 = 4", "parameter TAP3 = -1"),
            ),
        ),
        ("p_pulse_radar_signal", "wrong_threshold"): (
            "rtl/threshold_comparator.v",
            (("$signed(in_sample) >= $signed(threshold_value)", "$signed(in_sample) > $signed(threshold_value)"),),
        ),
        ("p_pulse_radar_signal", "off_by_one_peak"): (
            "rtl/peak_detector_core.v",
            ((
                "out_peak_value <= candidate_found ? (candidate_is_new_peak ? candidate_value : peak_value) : {WIDTH{1'b0}};",
                "out_peak_value <= candidate_found ? peak_value : {WIDTH{1'b0}};",
            ),),
        ),
        ("p_pulse_radar_signal", "top_in_ready_stuck_high"): (
            "rtl/top.v",
            (
                (
                    "wire threshold_last;",
                    "wire threshold_last;\n  wire pipeline_in_ready;\n  assign in_ready = 1'b1;",
                ),
                (".in_valid(in_valid),", ".in_valid(in_valid && pipeline_in_ready),"),
                (".in_ready(in_ready),", ".in_ready(pipeline_in_ready),"),
            ),
        ),
        ("p_pulse_radar_signal", "history_updates_while_stalled"): (
            "rtl/matched_filter_core.v",
            ((
                "        end\n      end\n    end\n  end\nendmodule",
                "        end\n      end\n    end else if (in_valid) begin\n"
                "      sample_d2 <= sample_d1;\n"
                "      sample_d1 <= sample_d0;\n"
                "      sample_d0 <= in_sample_extended;\n"
                "    end\n  end\nendmodule",
            ),),
        ),
        ("sobel_threshold", "swap_x_y_gradient"): (
            "rtl/sobel_threshold_core.v",
            (
                ("assign abs_gx = gx[10] ? -gx : gx;", "assign abs_gx = gy[10] ? -gy : gy;"),
                ("assign abs_gy = gy[10] ? -gy : gy;", "assign abs_gy = gx[10] ? -gx : gx;"),
            ),
        ),
        ("sobel_threshold", "wrong_border_policy"): (
            "rtl/top.v",
            (("if (row_index == 16'd0) begin\n            out_edge <= 1'b0;", "if (row_index == 16'd0) begin\n            out_edge <= 1'b1;"),),
        ),
        ("sobel_threshold", "wrong_threshold"): (
            "rtl/sobel_threshold_core.v",
            (("assign out_edge = magnitude >= THRESHOLD;", "assign out_edge = magnitude > THRESHOLD;"),),
        ),
        ("sobel_threshold", "accumulator_truncation"): (
            "rtl/sobel_threshold_core.v",
            (("assign magnitude = abs_gx + abs_gy;", "assign magnitude = {8'd0, abs_gx[3:0] + abs_gy[3:0]};"),),
        ),
        ("sobel_threshold", "input_backpressure_error"): (
            "rtl/top.v",
            (("(!produces_output || !out_valid || out_ready);", "1'b1;"),),
        ),
        ("sobel_threshold", "ignore_in_last"): (
            "rtl/top.v",
            (("final_input_last <= in_last;", "final_input_last <= in_last | 1'b1;"),),
        ),
        ("sobel_threshold", "ignore_subsequent_reset"): (
            "rtl/top.v",
            (
                (
                    "reg [15:0] bottom_flush_column;",
                    "reg [15:0] bottom_flush_column;\n  reg mutation_reset_seen;",
                ),
                (
                    "always @(posedge clk or negedge rst_n) begin\n    if (!rst_n) begin\n      row_index",
                    "always @(posedge clk or negedge rst_n) begin\n"
                    "    if (!rst_n && mutation_reset_seen !== 1'b1) begin\n"
                    "      mutation_reset_seen <= 1'b1;\n"
                    "      row_index",
                ),
            ),
        ),
        ("p_vision_defect_core", "wrong_line_order"): (
            "rtl/sobel_window.v",
            (("assign select_line0 = !row_index[0];", "assign select_line0 = 1'b0;"),),
        ),
        ("p_vision_defect_core", "wrong_threshold"): (
            "rtl/sobel_threshold_core.v",
            (("assign out_edge = magnitude >= THRESHOLD;", "assign out_edge = magnitude > THRESHOLD;"),),
        ),
        ("p_vision_defect_core", "missing_defect"): (
            "rtl/vision_defect_accumulator.v",
            (("pixel_accept && pixel_edge && !defect_present", "pixel_accept && pixel_edge && !defect_present && 1'b0"),),
        ),
        ("p_vision_defect_core", "wrong_bbox"): (
            "rtl/vision_defect_accumulator.v",
            (("first_defect_x <= pixel_x;", "first_defect_x <= pixel_x + 16'd1;"),),
        ),
        ("p_vision_defect_core", "hardcoded_first_coordinate"): (
            "rtl/vision_defect_accumulator.v",
            (
                (
                    "first_defect_x <= pixel_x;",
                    "first_defect_x <= pixel_x[0] ? pixel_x : pixel_x - 16'd1;",
                ),
                (
                    "first_defect_y <= pixel_y;",
                    "first_defect_y <= pixel_y[0] ? pixel_y : pixel_y + 16'd1;",
                ),
            ),
        ),
        ("p_vision_defect_core", "input_backpressure_error"): (
            "rtl/top.v",
            (("(!produces_output || !out_valid || out_ready);", "1'b1;"),),
        ),
        ("p_vision_defect_core", "ignore_in_last"): (
            "rtl/top.v",
            (("final_input_last <= in_last;", "final_input_last <= in_last | 1'b1;"),),
        ),
        ("p_vision_defect_core", "ignore_subsequent_reset"): (
            "rtl/top.v",
            (
                (
                    "reg [15:0] bottom_flush_column;",
                    "reg [15:0] bottom_flush_column;\n  reg mutation_reset_seen;",
                ),
                (
                    "always @(posedge clk or negedge rst_n) begin\n    if (!rst_n) begin\n      row_index",
                    "always @(posedge clk or negedge rst_n) begin\n"
                    "    if (!rst_n && mutation_reset_seen !== 1'b1) begin\n"
                    "      mutation_reset_seen <= 1'b1;\n"
                    "      row_index",
                ),
            ),
        ),
        ("pattern_matcher", "wrong_pattern_order"): (
            "rtl/pattern_matcher.v",
            (("token0 == TOKEN0 && token1 == TOKEN1 && token2 == TOKEN2", "token0 == TOKEN2 && token1 == TOKEN1 && token2 == TOKEN0"),),
        ),
        ("pattern_matcher", "false_positive"): (
            "rtl/pattern_matcher.v",
            (("in_data == TOKEN3", "in_data != TOKEN3"),),
        ),
        ("pattern_matcher", "miss_overlap"): (
            "rtl/pattern_matcher.v",
            (("token0 <= token1;", "token0 <= {WIDTH{1'b0}};"),),
        ),
        ("pattern_matcher", "missing_stall"): (
            "rtl/pattern_matcher.v",
            (("assign in_ready = !match_valid || match_ready;", "assign in_ready = !match_valid || match_ready || match_valid;"),),
        ),
        ("p_stream_trigger_filter", "wrong_pattern_order"): (
            "rtl/pattern_matcher.v",
            (("token0 == TOKEN0 && token1 == TOKEN1 && token2 == TOKEN2", "token0 == TOKEN2 && token1 == TOKEN1 && token2 == TOKEN0"),),
        ),
        ("p_stream_trigger_filter", "false_trigger"): (
            "rtl/trigger_fsm.v",
            (("trigger_valid <= match_valid;", "trigger_valid <= 1'b1;"),),
        ),
        ("p_stream_trigger_filter", "missing_backpressure"): (
            "rtl/stream_packer.v",
            (("assign event_ready = !out_valid || out_ready;", "assign event_ready = !out_valid || out_ready || out_valid;"),),
        ),
        ("p_stream_trigger_filter", "drop_transaction"): (
            "rtl/stream_packer.v",
            (("out_match_word <= event_word;", "out_match_word <= event_word ^ event_word;"),),
        ),
        ("qtable_update_core", "wrong_td_formula"): (
            "rtl/td_update_core.v",
            (("assign td_error_full = discounted_return -", "assign td_error_full = discounted_return +"),),
        ),
        ("qtable_update_core", "accumulator_truncation"): (
            "rtl/td_update_core.v",
            (
                (
                    "assign td_error_full = discounted_return -\n"
                    "    {{(DATA_WIDTH+1){value[DATA_WIDTH-1]}}, value};",
                    "assign td_error_full =\n"
                    "    {{((2*DATA_WIDTH)-3){discounted_return[3]}}, discounted_return[3:0]} +\n"
                    "    {{(2*DATA_WIDTH){1'b0}}, ^discounted_return[(2*DATA_WIDTH):4]} -\n"
                    "    {{(DATA_WIDTH+1){value[DATA_WIDTH-1]}}, value};",
                ),
            ),
        ),
        ("qtable_update_core", "wrong_signed_shift"): (
            "rtl/discount_core.v",
            (("gamma_next_product >>> SCALE_SHIFT", "gamma_next_product >> SCALE_SHIFT"),),
        ),
        ("qtable_update_core", "missing_saturation"): (
            "rtl/td_update_core.v",
            (
                (
                    "assign updated_value =\n"
                    "    (!updated_value_full[DATA_WIDTH] && updated_value_full[DATA_WIDTH-1]) ?\n"
                    "      {1'b0, {(DATA_WIDTH-1){1'b1}}} :\n"
                    "    (updated_value_full[DATA_WIDTH] && !updated_value_full[DATA_WIDTH-1]) ?\n"
                    "      {1'b1, {(DATA_WIDTH-1){1'b0}}} :\n"
                    "      updated_value_full[DATA_WIDTH-1:0];",
                    "assign updated_value =\n"
                    "    updated_value_full[DATA_WIDTH] ?\n"
                    "      updated_value_full[DATA_WIDTH-1:0] :\n"
                    "      updated_value_full[DATA_WIDTH-1:0];",
                ),
            ),
        ),
        ("p_rl_qlearning_accel", "wrong_td_formula"): (
            "rtl/td_update_core.v",
            (
                (
                    "$signed({2'b00, next_value}) -\n"
                    "                         $signed({2'b00, value_estimate});",
                    "$signed({2'b00, next_value}) +\n"
                    "                         $signed({2'b00, value_estimate});",
                ),
            ),
        ),
        ("p_rl_qlearning_accel", "wrong_argmax_tie_break"): (
            "rtl/policy_value_core.v",
            (("assign selected_action = (score1 > score0)", "assign selected_action = (score1 >= score0)"),),
        ),
        ("p_rl_qlearning_accel", "accumulator_truncation"): (
            "rtl/td_update_core.v",
            (
                (
                    "assign update_product = alpha * td_error_nonnegative;",
                    "assign update_product = (alpha * td_error_nonnegative) &\n"
                    "                          {{((2*DATA_WIDTH)-3){1'b0}}, 4'hf};",
                ),
            ),
        ),
        ("p_rl_qlearning_accel", "missing_done"): (
            "rtl/result_stream_stage.v",
            (("episode_done_out <= done_in;", "episode_done_out <= done_in && 1'b0;"),),
        ),
        ("p_rl_qlearning_accel", "wrong_register_offset"): (
            "rtl/host_config_bank.v",
            (("3'd0: weight0 <= cfg_data;", "3'd0: bias0 <= cfg_data;"),),
        ),
        ("matrix_vector_mac", "wrong_index_order"): (
            "rtl/dot_product_engine.v",
            ((".addr(index)", ".addr(2'd3 - index)"),),
        ),
        ("matrix_vector_mac", "truncate_accumulator"): (
            "rtl/dot_product_engine.v",
            ((
                "accum <= next_accum;",
                "accum <= {{(RESULT_WIDTH-WIDTH){next_accum[WIDTH-1]}}, next_accum[WIDTH-1:0]};",
            ),),
        ),
        ("matrix_vector_mac", "wrong_lane_reduction"): (
            "rtl/dot_product_engine.v",
            (("result <= next_accum;", "result <= accum;"),),
        ),
        ("matrix_vector_mac", "missing_stall"): (
            "rtl/dot_product_engine.v",
            ((
                "assign sample_ready = !result_valid || result_ready;",
                "assign sample_ready = 1'b1;",
            ),),
        ),
        ("uart_tx", "wrong_bit_order"): (
            "rtl/uart_tx_core.v",
            (
                ("tx <= shifter[0];", "tx <= shifter[7];"),
                ("shifter <= {1'b0, shifter[7:1]};", "shifter <= {shifter[6:0], 1'b0};"),
            ),
        ),
        ("uart_tx", "missing_stop_bit"): (
            "rtl/uart_tx_core.v",
            (("STOP: begin\n          if (baud_tick) begin\n            tx <= 1'b1;", "STOP: begin\n          if (baud_tick) begin\n            tx <= 1'b0;"),),
        ),
        ("uart_tx", "wrong_baud_tick"): (
            "rtl/uart_tx_core.v",
            (("DATA: begin\n          if (baud_tick) begin", "DATA: begin\n          if (1'b1) begin"),),
        ),
        ("uart_rx", "wrong_sampling_point"): (
            "rtl/uart_rx_core.v",
            (("localparam [15:0] HALF_CLKS_PER_BIT = CLKS_PER_BIT_16 / 2;", "localparam [15:0] HALF_CLKS_PER_BIT = 16'd1;"),),
        ),
        ("uart_rx", "ignore_start_bit"): (
            "rtl/uart_rx_core.v",
            (("if (!rx) begin\n              bit_index <= 3'd0;", "if (1'b1) begin\n              bit_index <= 3'd0;"),),
        ),
        ("uart_rx", "wrong_shift_direction"): (
            "rtl/uart_rx_core.v",
            (("data[bit_index] <= rx;", "data[3'd7 - bit_index] <= rx;"),),
        ),
        ("uart_fifo_loopback", "fifo_drop_byte"): (
            "rtl/top.v",
            ((
                ".wr_en(rx_data_valid && !fifo_full && !rx_framing_error),",
                ".wr_en(rx_data_valid && !fifo_full && !rx_framing_error && 1'b0),",
            ),),
        ),
        ("uart_fifo_loopback", "wrong_uart_bit_order"): (
            "rtl/uart_tx_core.v",
            (
                ("tx <= shifter[0];", "tx <= shifter[7];"),
                ("tx <= shifter[bit_index + 3'd1];", "tx <= shifter[3'd6 - bit_index];"),
            ),
        ),
        ("uart_fifo_loopback", "fifo_order_swap"): (
            "rtl/sync_fifo_core.v",
            (("assign dout = mem[rd_ptr];", "assign dout = mem[rd_ptr + 2'd1];"),),
        ),
        ("spi_master", "wrong_bit_order"): (
            "rtl/spi_master_core.v",
            (
                ("tx_shift <= {tx_data[6:0], 1'b0};", "tx_shift <= {1'b0, tx_data[7:1]};"),
                ("mosi <= tx_data[7];", "mosi <= tx_data[0];"),
                ("mosi <= tx_shift[7];", "mosi <= tx_shift[0];"),
                ("tx_shift <= {tx_shift[6:0], 1'b0};", "tx_shift <= {1'b0, tx_shift[7:1]};"),
            ),
        ),
        ("spi_master", "cpol_cpha_mismatch"): (
            "rtl/spi_master_core.v",
            (("if (sclk == 1'b0) begin", "if (sclk == 1'b1) begin"),),
        ),
        ("spi_master", "missing_cs_framing"): (
            "rtl/spi_master_core.v",
            (("busy <= 1'b1;\n          cs_n <= 1'b0;", "busy <= 1'b1;\n          cs_n <= 1'b1;"),),
        ),
    }
    replacement = replacements.get((family_id, mutation_name))
    if replacement is None:
        return None
    path, edits = replacement
    source = files.get(path)
    if source is None or any(old not in source for old, _ in edits):
        return None
    updated = dict(files)
    for old, new in edits:
        source = source.replace(old, new, 1)
    updated[path] = source
    return updated


def _rename_reset_port(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    top_path = "rtl/top.v"
    top_rtl = updated.get(top_path)
    if top_rtl is None:
        raise ValueError("rename_reset_port requires rtl/top.v")
    updated[top_path] = top_rtl.replace("rst_n", "reset_n", 1)
    return updated


def _undefined_signal_reference(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    top_path = "rtl/top.v"
    top_rtl = updated.get(top_path)
    if top_rtl is None:
        raise ValueError("undefined_signal_reference requires rtl/top.v")
    updated[top_path] = _replace_once(
        top_rtl,
        "count <= count +",
        "count <= missing_count +",
        "undefined_signal_reference requires counter update logic",
    )
    return updated


def _missing_manifest_source(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    manifest = _load_manifest(updated)
    sources = list(manifest["sources"])
    missing_source = "rtl/missing_dependency.v"
    if missing_source not in sources:
        sources.append(missing_source)
    manifest["sources"] = sources
    updated["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return updated


def _wrong_top_module(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    manifest = _load_manifest(updated)
    manifest["top_module"] = "missing_top"
    updated["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return updated


def _width_mismatch(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    top_path = "rtl/top.v"
    top_rtl = updated.get(top_path)
    if top_rtl is None:
        raise ValueError("width_mismatch requires rtl/top.v")
    match = re.search(r"output reg \[(\d+):0\] count", top_rtl)
    if match is None:
        raise ValueError("width_mismatch requires a counter-style count port")
    old = match.group(0)
    new = f"output reg [{int(match.group(1)) + 1}:0] count"
    updated[top_path] = top_rtl.replace(old, new, 1)
    return updated


def _testbench_expected_value_mismatch(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    testbench_path = "sim/tb_top.v"
    testbench = updated.get(testbench_path)
    if testbench is None:
        raise ValueError("testbench_expected_value_mismatch requires sim/tb_top.v")
    updated[testbench_path] = _replace_once(
        testbench,
        "count !== 4'd4",
        "count !== 4'd5",
        "testbench_expected_value_mismatch requires a 4-bit counter self-check",
    )
    return updated


def _constraint_missing_clock(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    sdc_path = "constraints/timing.sdc"
    if sdc_path not in updated:
        raise ValueError("constraint_missing_clock requires constraints/timing.sdc")
    updated[sdc_path] = "create_clock -name missing_clk -period 10.000 [get_ports missing_clk]\n"
    return updated


def _multimodule_connection_mismatch(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    top_path = "rtl/top.v"
    top_rtl = updated.get(top_path)
    if top_rtl is None:
        raise ValueError("multimodule_connection_mismatch requires rtl/top.v")
    replacements = [
        ("uart_tx_core u_uart_tx_core", "uart_tx_core_missing u_uart_tx_core"),
        ("spi_master_core u_spi_master_core", "spi_master_core_missing u_spi_master_core"),
        ("pwm_channel u_pwm_channel", "pwm_channel_missing u_pwm_channel"),
        ("fir_filter_core u_fir_filter_core", "fir_filter_core_missing u_fir_filter_core"),
        ("stream_stage u_stream_stage", "stream_stage_missing u_stream_stage"),
        ("dot_product_engine u_dot_product_engine", "dot_product_engine_missing u_dot_product_engine"),
    ]
    for old, new in replacements:
        if old in top_rtl:
            updated[top_path] = top_rtl.replace(old, new, 1)
            return updated
    raise ValueError("multimodule_connection_mismatch requires a known multi-module top instantiation")


def _replace_once(text: str, old: str, new: str, error_message: str) -> str:
    if old not in text:
        raise ValueError(error_message)
    return text.replace(old, new, 1)


def _load_manifest(files: dict[str, str]) -> dict[str, object]:
    try:
        manifest = json.loads(files["manifest.json"])
    except KeyError as exc:
        raise ValueError("failure injector requires manifest.json") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc.msg}") from exc
    if not isinstance(manifest.get("sources"), list):
        raise ValueError("manifest.json must contain sources list")
    return manifest
