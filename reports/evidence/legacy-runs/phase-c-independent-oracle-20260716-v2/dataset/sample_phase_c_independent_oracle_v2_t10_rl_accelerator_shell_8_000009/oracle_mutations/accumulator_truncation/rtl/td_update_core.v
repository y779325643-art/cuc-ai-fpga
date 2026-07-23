module td_update_core #(
    parameter DATA_WIDTH = 8
) (
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] next_value,
    input wire [DATA_WIDTH-1:0] value_estimate,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] updated_value
);

  wire signed [DATA_WIDTH+1:0] td_error_full;
  wire [DATA_WIDTH:0] td_error_nonnegative;
  wire [(2*DATA_WIDTH):0] update_product;
  wire [(2*DATA_WIDTH):0] update_delta_full;
  wire [DATA_WIDTH-1:0] update_delta;
  wire update_delta_round;
  wire update_delta_overflow;

  assign td_error_full = $signed({2'b00, reward}) +
                         $signed({2'b00, next_value}) -
                         $signed({2'b00, value_estimate});
  assign td_error_nonnegative = td_error_full[DATA_WIDTH+1] ?
                                {(DATA_WIDTH+1){1'b0}} :
                                td_error_full[DATA_WIDTH:0];
  assign update_product = (alpha * td_error_nonnegative) &
                          {{((2*DATA_WIDTH)-3){1'b0}}, 4'hf};
  assign update_delta_full = update_product >> 4;
  assign update_delta_round = |update_product[3:0];
  assign update_delta_overflow = |update_delta_full[(2*DATA_WIDTH):DATA_WIDTH];
  assign update_delta = update_delta_overflow ? {DATA_WIDTH{1'b1}} :
                        update_delta_full[DATA_WIDTH-1:0];
  assign updated_value = value_estimate + update_delta;
  assign out_valid = in_valid | (update_delta_round & in_valid);

endmodule
