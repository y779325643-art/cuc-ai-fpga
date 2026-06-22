module top (
    input wire clk,
    input wire rst_n,
    input wire start,
    output wire busy,
    output wire done,
    output wire [11:0] result
);

  // dot_product_engine contains mac_unit and vector_rom instances.
  dot_product_engine #(
    .WIDTH(8),
    .RESULT_WIDTH(12)
  ) u_dot_product_engine (
    .clk(clk),
    .rst_n(rst_n),
    .start(start),
    .busy(busy),
    .done(done),
    .result(result)
  );

endmodule
