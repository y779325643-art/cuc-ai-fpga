module top (
    input wire clk,
    input wire rst_n,
    input wire cfg_valid,
    output wire cfg_ready,
    input wire [2:0] cfg_addr,
    input wire [7:0] cfg_data,
    input wire obs_valid,
    output wire obs_ready,
    input wire [7:0] obs0,
    input wire [7:0] obs1,
    output wire action_valid,
    input wire action_ready,
    output wire selected_action,
    output wire [7:0] value_estimate
);

  wire [7:0] weight0;
  wire [7:0] weight1;
  wire [7:0] bias0;
  wire [7:0] bias1;
  wire enable;
  wire obs_stage_valid;
  wire obs_stage_ready;
  wire [7:0] obs0_s;
  wire [7:0] obs1_s;
  wire score_valid;
  wire score_ready;
  wire [7:0] policy_score0;
  wire [7:0] policy_score1;
  wire select_valid;
  wire select_ready;
  wire select_action;
  wire [7:0] select_value;

  config_reg_bank #(
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8)
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
