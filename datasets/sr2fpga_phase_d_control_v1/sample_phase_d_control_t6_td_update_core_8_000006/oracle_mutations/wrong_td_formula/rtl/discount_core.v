module discount_core #(
    parameter DATA_WIDTH = 8,
    parameter SCALE_SHIFT = 4
) (
    input wire in_valid,
    output wire in_ready,
    input wire signed [DATA_WIDTH-1:0] reward,
    input wire signed [DATA_WIDTH-1:0] next_value,
    input wire [DATA_WIDTH-1:0] gamma,
    output wire out_valid,
    input wire out_ready,
    output wire signed [(2*DATA_WIDTH):0] discounted_return
);

  wire signed [(2*DATA_WIDTH)-1:0] gamma_next_product;
  wire signed [(2*DATA_WIDTH)-1:0] discounted_next_full;
  wire discounted_next_round;

  assign in_ready = out_ready;
  assign out_valid = in_valid | (discounted_next_round & in_valid);
  assign gamma_next_product = $signed({1'b0, gamma}) * next_value;
  assign discounted_next_full = gamma_next_product >>> SCALE_SHIFT;
  assign discounted_next_round = |gamma_next_product[SCALE_SHIFT-1:0];
  assign discounted_return =
    {{(DATA_WIDTH+1){reward[DATA_WIDTH-1]}}, reward} +
    {discounted_next_full[(2*DATA_WIDTH)-1], discounted_next_full};

endmodule
