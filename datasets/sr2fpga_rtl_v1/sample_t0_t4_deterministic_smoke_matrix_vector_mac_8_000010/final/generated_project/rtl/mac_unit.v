module mac_unit #(
    parameter WIDTH = 8,
    parameter ACC_WIDTH = 12
) (
    input wire [WIDTH-1:0] sample,
    input wire [1:0] coefficient,
    input wire [ACC_WIDTH-1:0] accum,
    output wire [ACC_WIDTH-1:0] result
);

  wire [ACC_WIDTH-1:0] extended_sample;
  wire [ACC_WIDTH-1:0] product_x1;
  wire [ACC_WIDTH-1:0] product_x2;

  assign extended_sample = {{(ACC_WIDTH-WIDTH){1'b0}}, sample};
  assign product_x1 = coefficient[0] ? extended_sample : {ACC_WIDTH{1'b0}};
  assign product_x2 = coefficient[1] ? (extended_sample << 1) : {ACC_WIDTH{1'b0}};
  assign result = accum + product_x1 + product_x2;

endmodule
