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
  wire [DATA_WIDTH-1:0] input_stage__reward_i;
  wire [DATA_WIDTH-1:0] input_stage__value_i;
  wire [DATA_WIDTH-1:0] input_stage__next_value_i;
  wire [DATA_WIDTH-1:0] input_stage__gamma_i;
  wire [DATA_WIDTH-1:0] input_stage__alpha_i;
  wire input_stage__tuple_valid_o;
  wire input_stage__tuple_ready_i;
  wire [DATA_WIDTH-1:0] input_stage__reward_o;
  wire [DATA_WIDTH-1:0] input_stage__value_o;
  wire [DATA_WIDTH-1:0] input_stage__next_value_o;
  wire [DATA_WIDTH-1:0] input_stage__gamma_o;
  wire [DATA_WIDTH-1:0] input_stage__alpha_o;
  wire [DATA_WIDTH-1:0] discount__next_value_i;
  wire [DATA_WIDTH-1:0] discount__gamma_i;
  wire [DATA_WIDTH-1:0] discount__discounted_next_value_o;
  wire [DATA_WIDTH-1:0] update__reward_i;
  wire [DATA_WIDTH-1:0] update__value_i;
  wire [DATA_WIDTH-1:0] update__alpha_i;
  wire [DATA_WIDTH-1:0] update__discounted_next_value_i;
  wire [DATA_WIDTH-1:0] update__td_error_o;
  wire [DATA_WIDTH-1:0] update__updated_value_o;
  wire output_stage__result_valid_i;
  wire output_stage__result_ready_o;
  wire [DATA_WIDTH-1:0] output_stage__td_error_i;
  wire [DATA_WIDTH-1:0] output_stage__updated_value_i;
  wire output_stage__out_valid;
  wire output_stage__out_ready;
  wire [DATA_WIDTH-1:0] output_stage__td_error_o;
  wire [DATA_WIDTH-1:0] output_stage__updated_value_o;

  assign input_stage__reward_i = alpha;
  assign discount__next_value_i = input_stage__gamma_o;
  assign discount__discounted_next_value_o = input_stage__alpha_o;
  assign update__reward_i = discount__discounted_next_value_o;
  assign output_stage__td_error_i = update__updated_value_o;
  assign td_error = output_stage__updated_value_o;

  td_input_stage #(.DATA_WIDTH(DATA_WIDTH)) input_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(input_stage__in_valid),
    .in_ready(input_stage__in_ready),
    .reward_i(input_stage__reward_i),
    .value_i(input_stage__value_i),
    .next_value_i(input_stage__next_value_i),
    .gamma_i(input_stage__gamma_i),
    .alpha_i(input_stage__alpha_i),
    .tuple_valid_o(input_stage__tuple_valid_o),
    .tuple_ready_i(input_stage__tuple_ready_i),
    .reward_o(input_stage__reward_o),
    .value_o(input_stage__value_o),
    .next_value_o(input_stage__next_value_o),
    .gamma_o(input_stage__gamma_o),
    .alpha_o(input_stage__alpha_o)
  );

  discount_core #(.DATA_WIDTH(DATA_WIDTH)) discount (
    .next_value_i(discount__next_value_i),
    .gamma_i(discount__gamma_i),
    .discounted_next_value_o(discount__discounted_next_value_o)
  );

  td_update_core #(.DATA_WIDTH(DATA_WIDTH)) update (
    .reward_i(update__reward_i),
    .value_i(update__value_i),
    .alpha_i(update__alpha_i),
    .discounted_next_value_i(update__discounted_next_value_i),
    .td_error_o(update__td_error_o),
    .updated_value_o(update__updated_value_o)
  );

  stream_stage #(.DATA_WIDTH(DATA_WIDTH)) output_stage (
    .clk(clk),
    .rst_n(rst_n),
    .result_valid_i(output_stage__result_valid_i),
    .result_ready_o(output_stage__result_ready_o),
    .td_error_i(output_stage__td_error_i),
    .updated_value_i(output_stage__updated_value_i),
    .out_valid(output_stage__out_valid),
    .out_ready(output_stage__out_ready),
    .td_error_o(output_stage__td_error_o),
    .updated_value_o(output_stage__updated_value_o)
  );

endmodule
