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
    output wire signed [17:0] peak_value,
    output wire [17:0] peak_index
);

  wire correlation_valid;
  wire correlation_ready;
  wire signed [17:0] correlation;
  wire correlation_last;
  wire threshold_valid;
  wire threshold_ready;
  wire signed [17:0] thresholded_correlation;
  wire threshold_last;
  wire pipeline_in_ready;
  assign in_ready = 1'b1;

  matched_filter_core #(
    .WIDTH(8),
    .ACC_WIDTH(18)
  ) u_matched_filter_core (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid && pipeline_in_ready),
    .in_ready(pipeline_in_ready),
    .in_sample(in_sample),
    .in_last(in_last),
    .out_valid(correlation_valid),
    .out_ready(correlation_ready),
    .out_correlation(correlation),
    .out_last(correlation_last)
  );

  threshold_comparator #(
    .ACC_WIDTH(18),
    .THRESHOLD(10)
  ) u_threshold_comparator (
    .in_valid(correlation_valid),
    .in_ready(correlation_ready),
    .in_sample(correlation),
    .in_last(correlation_last),
    .out_valid(threshold_valid),
    .out_ready(threshold_ready),
    .out_sample(thresholded_correlation),
    .out_last(threshold_last)
  );

  peak_detector_core #(
    .WIDTH(18),
    .THRESHOLD(10)
  ) u_peak_detector_core (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(threshold_valid),
    .in_ready(threshold_ready),
    .in_sample(thresholded_correlation),
    .in_last(threshold_last),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_peak_found(peak_found),
    .out_peak_value(peak_value),
    .out_peak_index(peak_index)
  );
endmodule
