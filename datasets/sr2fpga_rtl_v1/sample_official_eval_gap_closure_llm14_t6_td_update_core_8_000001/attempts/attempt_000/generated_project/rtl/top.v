module top #(parameter DATA_WIDTH = 8, parameter SCALE_SHIFT = 4) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [7:0] reward,
    input wire [7:0] value,
    input wire [7:0] next_value,
    input wire [7:0] gamma,
    input wire [7:0] alpha,
    input wire out_ready,
    output wire in_ready,
    output wire out_valid,
    output wire [7:0] td_error,
    output wire [7:0] updated_value
);

  wire u_td_input_stage__in_valid;
  wire u_td_input_stage__in_ready;
  wire [DATA_WIDTH-1:0] u_td_input_stage__reward;
  wire [DATA_WIDTH-1:0] u_td_input_stage__value;
  wire [DATA_WIDTH-1:0] u_td_input_stage__next_value;
  wire [DATA_WIDTH-1:0] u_td_input_stage__gamma;
  wire [DATA_WIDTH-1:0] u_td_input_stage__alpha;
  wire u_td_input_stage__out_valid;
  wire u_td_input_stage__out_ready;
  wire [DATA_WIDTH-1:0] u_td_input_stage__reward_out;
  wire [DATA_WIDTH-1:0] u_td_input_stage__value_out;
  wire [DATA_WIDTH-1:0] u_td_input_stage__next_value_out;
  wire [DATA_WIDTH-1:0] u_td_input_stage__gamma_out;
  wire [DATA_WIDTH-1:0] u_td_input_stage__alpha_out;
  wire u_discount_core__in_valid;
  wire u_discount_core__in_ready;
  wire [DATA_WIDTH-1:0] u_discount_core__reward;
  wire [DATA_WIDTH-1:0] u_discount_core__next_value;
  wire [DATA_WIDTH-1:0] u_discount_core__gamma;
  wire u_discount_core__out_valid;
  wire u_discount_core__out_ready;
  wire [DATA_WIDTH-1:0] u_discount_core__discounted_return;
  wire u_td_update_core__in_valid;
  wire u_td_update_core__in_ready;
  wire [DATA_WIDTH-1:0] u_td_update_core__discounted_return;
  wire [DATA_WIDTH-1:0] u_td_update_core__value;
  wire [DATA_WIDTH-1:0] u_td_update_core__alpha;
  wire u_td_update_core__out_valid;
  wire u_td_update_core__out_ready;
  wire [DATA_WIDTH-1:0] u_td_update_core__td_error;
  wire [DATA_WIDTH-1:0] u_td_update_core__updated_value;
  wire u_stream_stage__in_valid;
  wire u_stream_stage__in_ready;
  wire [DATA_WIDTH-1:0] u_stream_stage__td_error;
  wire [DATA_WIDTH-1:0] u_stream_stage__updated_value;
  wire u_stream_stage__out_valid;
  wire u_stream_stage__out_ready;
  wire [DATA_WIDTH-1:0] u_stream_stage__td_error_out;
  wire [DATA_WIDTH-1:0] u_stream_stage__updated_value_out;

  assign u_td_input_stage__in_valid = in_valid;
  assign in_ready = u_td_input_stage__in_ready;
  assign u_td_input_stage__reward = reward;
  assign u_td_input_stage__value = value;
  assign u_td_input_stage__next_value = next_value;
  assign u_td_input_stage__gamma = gamma;
  assign u_td_input_stage__alpha = alpha;
  assign u_discount_core__in_valid = u_td_input_stage__out_valid;
  assign u_td_input_stage__out_ready = u_discount_core__in_ready;
  assign u_discount_core__reward = u_td_input_stage__reward_out;
  assign u_discount_core__next_value = u_td_input_stage__next_value_out;
  assign u_discount_core__gamma = u_td_input_stage__gamma_out;
  assign u_td_update_core__in_valid = u_discount_core__out_valid;
  assign u_discount_core__out_ready = u_td_update_core__in_ready;
  assign u_td_update_core__discounted_return = u_discount_core__discounted_return;
  assign u_td_update_core__value = u_td_input_stage__value_out;
  assign u_td_update_core__alpha = u_td_input_stage__alpha_out;
  assign u_stream_stage__in_valid = u_td_update_core__out_valid;
  assign u_td_update_core__out_ready = u_stream_stage__in_ready;
  assign u_stream_stage__td_error = u_td_update_core__td_error;
  assign u_stream_stage__updated_value = u_td_update_core__updated_value;
  assign out_valid = u_stream_stage__out_valid;
  assign u_stream_stage__out_ready = out_ready;
  assign td_error = u_stream_stage__td_error_out;
  assign updated_value = u_stream_stage__updated_value_out;

  td_input_stage #(.DATA_WIDTH(DATA_WIDTH)) u_td_input_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(u_td_input_stage__in_valid),
    .in_ready(u_td_input_stage__in_ready),
    .reward(u_td_input_stage__reward),
    .value(u_td_input_stage__value),
    .next_value(u_td_input_stage__next_value),
    .gamma(u_td_input_stage__gamma),
    .alpha(u_td_input_stage__alpha),
    .out_valid(u_td_input_stage__out_valid),
    .out_ready(u_td_input_stage__out_ready),
    .reward_out(u_td_input_stage__reward_out),
    .value_out(u_td_input_stage__value_out),
    .next_value_out(u_td_input_stage__next_value_out),
    .gamma_out(u_td_input_stage__gamma_out),
    .alpha_out(u_td_input_stage__alpha_out)
  );

  discount_core #(.DATA_WIDTH(DATA_WIDTH), .SCALE_SHIFT(SCALE_SHIFT)) u_discount_core (
    .in_valid(u_discount_core__in_valid),
    .in_ready(u_discount_core__in_ready),
    .reward(u_discount_core__reward),
    .next_value(u_discount_core__next_value),
    .gamma(u_discount_core__gamma),
    .out_valid(u_discount_core__out_valid),
    .out_ready(u_discount_core__out_ready),
    .discounted_return(u_discount_core__discounted_return)
  );

  td_update_core #(.DATA_WIDTH(DATA_WIDTH), .SCALE_SHIFT(SCALE_SHIFT)) u_td_update_core (
    .in_valid(u_td_update_core__in_valid),
    .in_ready(u_td_update_core__in_ready),
    .discounted_return(u_td_update_core__discounted_return),
    .value(u_td_update_core__value),
    .alpha(u_td_update_core__alpha),
    .out_valid(u_td_update_core__out_valid),
    .out_ready(u_td_update_core__out_ready),
    .td_error(u_td_update_core__td_error),
    .updated_value(u_td_update_core__updated_value)
  );

  stream_stage #(.DATA_WIDTH(DATA_WIDTH)) u_stream_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(u_stream_stage__in_valid),
    .in_ready(u_stream_stage__in_ready),
    .td_error(u_stream_stage__td_error),
    .updated_value(u_stream_stage__updated_value),
    .out_valid(u_stream_stage__out_valid),
    .out_ready(u_stream_stage__out_ready),
    .td_error_out(u_stream_stage__td_error_out),
    .updated_value_out(u_stream_stage__updated_value_out)
  );

endmodule
