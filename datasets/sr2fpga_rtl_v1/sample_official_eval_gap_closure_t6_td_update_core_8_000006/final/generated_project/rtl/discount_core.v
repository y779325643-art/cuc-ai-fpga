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
    output wire signed [DATA_WIDTH-1:0] discounted_return
);

  wire signed [(2*DATA_WIDTH)-1:0] gamma_next_product;
  wire signed [DATA_WIDTH-1:0] discounted_next;

  assign in_ready = out_ready;
  assign out_valid = in_valid;
  assign gamma_next_product = $signed({1'b0, gamma}) * next_value;
  assign discounted_next = gamma_next_product >>> SCALE_SHIFT;
  assign discounted_return = reward + discounted_next;

endmodule
