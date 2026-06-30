module top (
    input wire clk,
    input wire rst_n,
    input wire cfg_valid,
    output wire cfg_ready,
    input wire [2:0] cfg_addr,
    input wire [7:0] cfg_data,
    input wire sample_valid,
    output wire sample_ready,
    input wire [7:0] obs0,
    input wire [7:0] obs1,
    input wire [7:0] reward,
    input wire [7:0] next_value,
    input wire done_in,
    output wire result_valid,
    input wire result_ready,
    output wire selected_action,
    output wire [7:0] value_estimate,
    output wire [7:0] updated_value,
    output wire episode_done,
    output wire irq
);

  wire [7:0] weight0;
  wire [7:0] bias0;
  wire [7:0] weight1;
  wire [7:0] bias1;
  wire [7:0] alpha;
  wire enable;
  wire sample_stage_valid;
  wire sample_consume_ready;
  wire [7:0] captured_obs0;
  wire [7:0] captured_obs1;
  wire [7:0] captured_reward;
  wire [7:0] captured_next_value;
  wire captured_done;
  wire policy_valid;
  wire policy_selected_action;
  wire [7:0] policy_value_estimate;
  wire update_valid;
  wire [7:0] update_updated_value;

  host_config_bank #(
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
