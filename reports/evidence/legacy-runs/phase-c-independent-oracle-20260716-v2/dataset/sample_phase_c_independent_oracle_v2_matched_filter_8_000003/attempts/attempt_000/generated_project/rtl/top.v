module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire signed [7:0] in_sample,
    output wire out_valid,
    input wire out_ready,
    output wire signed [17:0] correlation
);

  wire core_in_ready;
  wire ignored_last;
  assign in_ready = core_in_ready && !ignored_last;

  matched_filter_core #(
    .WIDTH(8),
    .ACC_WIDTH(18)
  ) u_matched_filter_core (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(core_in_ready),
    .in_sample(in_sample),
    .in_last(1'b0),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_correlation(correlation),
    .out_last(ignored_last)
  );

endmodule
