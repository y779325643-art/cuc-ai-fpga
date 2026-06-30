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
  wire [DATA_WIDTH-1:0] td_error_a_limited;
  wire [DATA_WIDTH-1:0] td_error_b_limited;
  wire [DATA_WIDTH-1:0] update_delta_a;
  wire [DATA_WIDTH-1:0] update_delta_b;
  wire update_delta_a_round;
  wire update_delta_b_round;
  wire update_delta_a_overflow;
  wire update_delta_b_overflow;

  assign td_error_a_full = {1'b0, reward_a} + {1'b0, next_value_a} - {1'b0, value_estimate_a};
  assign td_error_b_full = {1'b0, reward_b} + {1'b0, next_value_b} - {1'b0, value_estimate_b};
  assign td_error_a_limited = td_error_a_full[DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                              td_error_a_full[DATA_WIDTH-1:0];
  assign td_error_b_limited = td_error_b_full[DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                              td_error_b_full[DATA_WIDTH-1:0];
  assign update_product_a = alpha * td_error_a_limited;
  assign update_product_b = alpha * td_error_b_limited;
  assign update_delta_a_round = |update_product_a[3:0];
  assign update_delta_b_round = |update_product_b[3:0];
  assign update_delta_a_overflow = |update_product_a[(2*DATA_WIDTH)-1:DATA_WIDTH+4];
  assign update_delta_b_overflow = |update_product_b[(2*DATA_WIDTH)-1:DATA_WIDTH+4];
  assign update_delta_a = update_delta_a_overflow ? {DATA_WIDTH{1'b1}} :
                          update_product_a[DATA_WIDTH+3:4];
  assign update_delta_b = update_delta_b_overflow ? {DATA_WIDTH{1'b1}} :
                          update_product_b[DATA_WIDTH+3:4];
  assign updated_value_a = value_estimate_a + update_delta_a;
  assign updated_value_b = value_estimate_b + update_delta_b;
  assign out_valid = in_valid |
                     ((update_delta_a_round | update_delta_b_round) & in_valid);

endmodule
