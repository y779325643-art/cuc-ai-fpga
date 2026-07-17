module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire signed [7:0] reward,
    input wire signed [7:0] value,
    input wire signed [7:0] next_value,
    input wire [7:0] gamma,
    input wire [7:0] alpha,
    output wire out_valid,
    input wire out_ready,
    output wire signed [7:0] td_error,
    output wire signed [7:0] updated_value
);

  wire input_valid;
  wire input_ready;
  wire signed [7:0] reward_s;
  wire signed [7:0] value_s;
  wire signed [7:0] next_value_s;
  wire [7:0] gamma_s;
  wire [7:0] alpha_s;
  wire discount_valid;
  wire discount_ready;
  wire signed [16:0] discounted_return;
  wire update_valid;
  wire update_ready;
  wire signed [7:0] update_td_error;
  wire signed [7:0] update_value;

  td_input_stage #(
    .DATA_WIDTH(8)
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
    .DATA_WIDTH(8),
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
    .DATA_WIDTH(8),
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
    .DATA_WIDTH(8)
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
