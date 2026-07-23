module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire signed [7:0] in_sample,
    input wire in_last,
    output wire out_valid,
    input wire out_ready,
    output wire peak_found,
    output wire signed [7:0] peak_value,
    output wire [7:0] peak_index
);

  peak_detector_core #(
    .WIDTH(8),
    .THRESHOLD(10)
  ) u_peak_detector_core (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_sample(in_sample),
    .in_last(in_last),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_peak_found(peak_found),
    .out_peak_value(peak_value),
    .out_peak_index(peak_index)
  );
endmodule
