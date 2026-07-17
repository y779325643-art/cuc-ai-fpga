module top #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] value,
    input wire [DATA_WIDTH-1:0] next_value,
    input wire [DATA_WIDTH-1:0] gamma,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] td_error,
    output wire [DATA_WIDTH-1:0] updated_value
);

  wire input_stage__in_valid;
  wire input_stage__in_ready;
  wire [DATA_WIDTH-1:0] input_stage__reward;
  wire [DATA_WIDTH-1:0] input_stage__value;
  wire [DATA_WIDTH-1:0] input_stage__next_value;
  wire input_stage__tuple_valid;
  wire [DATA_WIDTH-1:0] input_stage__tuple_reward;
  wire [DATA_WIDTH-1:0] input_stage__tuple_value;
  wire [DATA_WIDTH-1:0] input_stage__tuple_next_value;
  wire [DATA_WIDTH-1:0] discount__gamma;
  wire [DATA_WIDTH-1:0] discount__next_value;
  wire [DATA_WIDTH-1:0] discount__discounted_value;
  wire [DATA_WIDTH-1:0] update__reward;
  wire [DATA_WIDTH-1:0] update__value;
  wire [DATA_WIDTH-1:0] update__discounted_value;
  wire [DATA_WIDTH-1:0] update__alpha;
  wire [DATA_WIDTH-1:0] update__td_error;
  wire [DATA_WIDTH-1:0] update__updated_value;
  wire output_stage__in_valid;
  wire output_stage__in_ready;
  wire [DATA_WIDTH-1:0] output_stage__td_error_in;
  wire [DATA_WIDTH-1:0] output_stage__updated_value_in;
  wire output_stage__out_valid;
  wire output_stage__out_ready;
  wire [DATA_WIDTH-1:0] output_stage__td_error_out;
  wire [DATA_WIDTH-1:0] output_stage__updated_value_out;

  assign input_stage__in_valid = next_value;
  assign input_stage__tuple_next_value = gamma;
  assign discount__gamma = input_stage__tuple_next_value;
  assign discount__discounted_value = input_stage__tuple_value;
  assign alpha = discount__discounted_value;
  assign update__reward = alpha;
  assign output_stage__td_error_in = update__updated_value;
  assign out_valid = output_stage__updated_value_out;
  wire _unused_data_flow_signals = &{1'b0, input_stage__in_ready, out_ready};

  td_input_stage #(.DATA_WIDTH(DATA_WIDTH)) input_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(input_stage__in_valid),
    .in_ready(input_stage__in_ready),
    .reward(input_stage__reward),
    .value(input_stage__value),
    .next_value(input_stage__next_value),
    .tuple_valid(input_stage__tuple_valid),
    .tuple_reward(input_stage__tuple_reward),
    .tuple_value(input_stage__tuple_value),
    .tuple_next_value(input_stage__tuple_next_value)
  );

  discount_core #(.DATA_WIDTH(DATA_WIDTH)) discount (
    .clk(clk),
    .rst_n(rst_n),
    .gamma(discount__gamma),
    .next_value(discount__next_value),
    .discounted_value(discount__discounted_value)
  );

  td_update_core #(.DATA_WIDTH(DATA_WIDTH)) update (
    .clk(clk),
    .rst_n(rst_n),
    .reward(update__reward),
    .value(update__value),
    .discounted_value(update__discounted_value),
    .alpha(update__alpha),
    .td_error(update__td_error),
    .updated_value(update__updated_value)
  );

  stream_stage #(.DATA_WIDTH(DATA_WIDTH)) output_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(output_stage__in_valid),
    .in_ready(output_stage__in_ready),
    .td_error_in(output_stage__td_error_in),
    .updated_value_in(output_stage__updated_value_in),
    .out_valid(output_stage__out_valid),
    .out_ready(output_stage__out_ready),
    .td_error_out(output_stage__td_error_out),
    .updated_value_out(output_stage__updated_value_out)
  );

endmodule
