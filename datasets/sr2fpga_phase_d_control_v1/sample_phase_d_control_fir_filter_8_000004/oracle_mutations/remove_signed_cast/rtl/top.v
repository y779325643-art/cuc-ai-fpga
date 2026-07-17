module top (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    output wire sample_ready,
    input wire signed [7:0] sample,
    output wire result_valid,
    input wire result_ready,
    output wire signed [10:0] result
);

  // fir_filter_core contains the mac_unit tap helpers.
  fir_filter_core #(
    .WIDTH(8),
    .RESULT_WIDTH(11)
  ) u_fir_filter_core (
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
