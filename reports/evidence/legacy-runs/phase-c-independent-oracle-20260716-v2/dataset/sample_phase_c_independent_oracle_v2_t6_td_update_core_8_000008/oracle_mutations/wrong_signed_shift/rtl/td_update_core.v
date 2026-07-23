module td_update_core #(
    parameter DATA_WIDTH = 8,
    parameter SCALE_SHIFT = 4
) (
    input wire in_valid,
    output wire in_ready,
    input wire signed [(2*DATA_WIDTH):0] discounted_return,
    input wire signed [DATA_WIDTH-1:0] value,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire out_valid,
    input wire out_ready,
    output wire signed [DATA_WIDTH-1:0] td_error,
    output wire signed [DATA_WIDTH-1:0] updated_value
);

  wire signed [(2*DATA_WIDTH):0] td_error_full;
  wire td_error_positive_overflow;
  wire td_error_negative_overflow;
  wire signed [(2*DATA_WIDTH):0] alpha_error_product;
  wire signed [(2*DATA_WIDTH):0] scaled_error_full;
  wire signed [DATA_WIDTH-1:0] scaled_error;
  wire signed [DATA_WIDTH:0] updated_value_full;
  wire scaled_error_round;
  wire scaled_error_positive_overflow;
  wire scaled_error_negative_overflow;

  assign in_ready = out_ready;
  assign out_valid = in_valid | (scaled_error_round & in_valid);
  assign td_error_full = discounted_return -
    {{(DATA_WIDTH+1){value[DATA_WIDTH-1]}}, value};
  assign td_error_positive_overflow =
    !td_error_full[2*DATA_WIDTH] && |td_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
  assign td_error_negative_overflow =
    td_error_full[2*DATA_WIDTH] && ~&td_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
  assign td_error = td_error_positive_overflow ? {1'b0, {(DATA_WIDTH-1){1'b1}}} :
                    (td_error_negative_overflow ? {1'b1, {(DATA_WIDTH-1){1'b0}}} :
                     td_error_full[DATA_WIDTH-1:0]);
  assign alpha_error_product = $signed({1'b0, alpha}) * td_error;
  assign scaled_error_full = alpha_error_product >>> SCALE_SHIFT;
  assign scaled_error_round = |alpha_error_product[SCALE_SHIFT-1:0];
  assign scaled_error_positive_overflow =
    !scaled_error_full[(2*DATA_WIDTH)-1] &&
    |scaled_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
  assign scaled_error_negative_overflow =
    scaled_error_full[(2*DATA_WIDTH)-1] &&
    ~&scaled_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
  assign scaled_error = scaled_error_positive_overflow ? {1'b0, {(DATA_WIDTH-1){1'b1}}} :
                        (scaled_error_negative_overflow ? {1'b1, {(DATA_WIDTH-1){1'b0}}} :
                         scaled_error_full[DATA_WIDTH-1:0]);
  assign updated_value_full =
    {value[DATA_WIDTH-1], value} + {scaled_error[DATA_WIDTH-1], scaled_error};
  assign updated_value =
    (!updated_value_full[DATA_WIDTH] && updated_value_full[DATA_WIDTH-1]) ?
      {1'b0, {(DATA_WIDTH-1){1'b1}}} :
    (updated_value_full[DATA_WIDTH] && !updated_value_full[DATA_WIDTH-1]) ?
      {1'b1, {(DATA_WIDTH-1){1'b0}}} :
      updated_value_full[DATA_WIDTH-1:0];

endmodule
