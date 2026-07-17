module mac_unit #(
    parameter WIDTH = 8,
    parameter ACC_WIDTH = 11
) (
    input wire [WIDTH-1:0] sample,
    input wire [2:0] coefficient,
    input wire signed [ACC_WIDTH-1:0] accum,
    output wire signed [ACC_WIDTH-1:0] result
);

  wire signed [ACC_WIDTH-1:0] product;

  assign product = $signed(sample) * $signed(coefficient);
  assign result = $signed(accum) + product;

endmodule
