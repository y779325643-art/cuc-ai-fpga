module top (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    output wire sample_ready,
    input wire signed [7:0] sample,
    output wire result_valid,
    input wire result_ready,
    output wire signed [11:0] result
);

  // dot_product_engine contains mac_unit and vector_rom instances.
  dot_product_engine #(
    .WIDTH(8),
    .RESULT_WIDTH(12)
  ) u_dot_product_engine (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(sample_valid),
    .sample_ready(sample_ready),
    .sample(sample),
    .result_valid(result_valid),
    .result_ready(result_ready),
    .result(result)
  );

endmodule
