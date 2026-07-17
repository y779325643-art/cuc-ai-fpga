module discount_core #(parameter DATA_WIDTH = 8) (
    input wire [DATA_WIDTH-1:0] next_value_i,
    input wire [DATA_WIDTH-1:0] gamma_i,
    output wire [DATA_WIDTH-1:0] discounted_next_value_o
);
  // SR2FPGA_BEHAVIOR_BEGIN
    localparam PRODUCT_WIDTH = DATA_WIDTH * 2;

    wire signed [DATA_WIDTH-1:0] next_value_signed;
    wire [DATA_WIDTH-1:0] gamma_unsigned;
    wire signed [PRODUCT_WIDTH:0] product_ext;
    wire signed [DATA_WIDTH:0] scaled_ext;
    wire [DATA_WIDTH-1:0] discounted_next_value_slice;
    wire _unused_discount_product_bits;

    assign next_value_signed = next_value_i;
    assign gamma_unsigned = gamma_i;
    assign product_ext = $signed(next_value_signed) * $signed({1'b0, gamma_unsigned});
    assign scaled_ext = product_ext[PRODUCT_WIDTH:DATA_WIDTH];
    assign discounted_next_value_slice = scaled_ext[DATA_WIDTH-1:0];
    assign _unused_discount_product_bits = ^product_ext[DATA_WIDTH-1:0];
    assign discounted_next_value_o = discounted_next_value_slice;
  // SR2FPGA_BEHAVIOR_END
endmodule
