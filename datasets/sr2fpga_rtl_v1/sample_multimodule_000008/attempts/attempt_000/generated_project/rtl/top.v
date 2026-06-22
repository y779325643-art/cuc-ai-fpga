module top (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [11:0] sample,
    output wire result_valid,
    output wire [14:0] result
);

  // fir_filter_core contains the mac_unit tap helpers.
  fir_filter_core #(
    .WIDTH(12),
    .RESULT_WIDTH(15)
  ) u_fir_filter_core (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(sample_valid),
    .sample(sample),
    .result_valid(result_valid),
    .result(result)
  );

endmodule
