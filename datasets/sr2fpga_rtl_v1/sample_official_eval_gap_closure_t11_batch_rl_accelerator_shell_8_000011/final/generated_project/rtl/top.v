module top (
    input wire clk,
    input wire rst_n,
    input wire cfg_valid,
    output wire cfg_ready,
    input wire [2:0] cfg_addr,
    input wire [7:0] cfg_data,
    input wire batch_valid,
    output wire batch_ready,
    input wire [7:0] obs0_a,
    input wire [7:0] obs1_a,
    input wire [7:0] reward_a,
    input wire [7:0] next_value_a,
    input wire done_a,
    input wire [7:0] obs0_b,
    input wire [7:0] obs1_b,
    input wire [7:0] reward_b,
    input wire [7:0] next_value_b,
    input wire done_b,
    output wire result_valid,
    input wire result_ready,
    output wire selected_action_a,
    output wire [7:0] value_estimate_a,
    output wire [7:0] updated_value_a,
    output wire selected_action_b,
    output wire [7:0] value_estimate_b,
    output wire [7:0] updated_value_b,
    output wire batch_done,
    output wire irq
);

  wire [7:0] weight0;
  wire [7:0] bias0;
  wire [7:0] weight1;
  wire [7:0] bias1;
  wire [7:0] alpha;
  wire enable;
  wire batch_stage_valid;
  wire batch_consume_ready;
  wire [7:0] captured_obs0_a;
  wire [7:0] captured_obs1_a;
  wire [7:0] captured_reward_a;
  wire [7:0] captured_next_value_a;
  wire captured_done_a;
  wire [7:0] captured_obs0_b;
  wire [7:0] captured_obs1_b;
  wire [7:0] captured_reward_b;
  wire [7:0] captured_next_value_b;
  wire captured_done_b;
  wire policy_valid;
  wire policy_selected_action_a;
  wire [7:0] policy_value_estimate_a;
  wire policy_selected_action_b;
  wire [7:0] policy_value_estimate_b;
  wire update_valid;
  wire [7:0] update_updated_value_a;
  wire [7:0] update_updated_value_b;

  batch_config_bank #(
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
