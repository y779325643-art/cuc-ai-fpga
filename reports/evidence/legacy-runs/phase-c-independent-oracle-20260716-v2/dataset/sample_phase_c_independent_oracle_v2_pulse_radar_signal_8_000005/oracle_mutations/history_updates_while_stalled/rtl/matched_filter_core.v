module matched_filter_core #(
    parameter WIDTH = 8,
    parameter ACC_WIDTH = 18,
    parameter TAP0 = -1,
    parameter TAP1 = 2,
    parameter TAP2 = -3,
    parameter TAP3 = 4
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire signed [WIDTH-1:0] in_sample,
    input wire in_last,
    output reg out_valid,
    input wire out_ready,
    output reg signed [ACC_WIDTH-1:0] out_correlation,
    output reg out_last
);

  wire signed [ACC_WIDTH-1:0] in_sample_extended;
  wire signed [ACC_WIDTH-1:0] tap0_value;
  wire signed [ACC_WIDTH-1:0] tap1_value;
  wire signed [ACC_WIDTH-1:0] tap2_value;
  wire signed [ACC_WIDTH-1:0] tap3_value;
  reg signed [ACC_WIDTH-1:0] sample_d0;
  reg signed [ACC_WIDTH-1:0] sample_d1;
  reg signed [ACC_WIDTH-1:0] sample_d2;
  wire signed [ACC_WIDTH-1:0] sum0;
  wire signed [ACC_WIDTH-1:0] sum1;
  wire signed [ACC_WIDTH-1:0] sum2;
  wire signed [ACC_WIDTH-1:0] correlation_sum;

  assign in_sample_extended = {{(ACC_WIDTH-WIDTH){in_sample[WIDTH-1]}}, in_sample};
  assign tap0_value = TAP0;
  assign tap1_value = TAP1;
  assign tap2_value = TAP2;
  assign tap3_value = TAP3;
  assign in_ready = !out_valid || out_ready;

  matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap0 (.sample(in_sample_extended), .coefficient(tap0_value), .accum({ACC_WIDTH{1'b0}}), .result(sum0));
  matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap1 (.sample(sample_d0), .coefficient(tap1_value), .accum(sum0), .result(sum1));
  matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap2 (.sample(sample_d1), .coefficient(tap2_value), .accum(sum1), .result(sum2));
  matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap3 (.sample(sample_d2), .coefficient(tap3_value), .accum(sum2), .result(correlation_sum));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sample_d0 <= {ACC_WIDTH{1'b0}};
      sample_d1 <= {ACC_WIDTH{1'b0}};
      sample_d2 <= {ACC_WIDTH{1'b0}};
      out_valid <= 1'b0;
      out_correlation <= {ACC_WIDTH{1'b0}};
      out_last <= 1'b0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        out_correlation <= correlation_sum;
        out_last <= in_last;
        if (in_last) begin
          sample_d0 <= {ACC_WIDTH{1'b0}};
          sample_d1 <= {ACC_WIDTH{1'b0}};
          sample_d2 <= {ACC_WIDTH{1'b0}};
        end else begin
          sample_d2 <= sample_d1;
          sample_d1 <= sample_d0;
          sample_d0 <= in_sample_extended;
        end
      end
    end else if (in_valid) begin
      sample_d2 <= sample_d1;
      sample_d1 <= sample_d0;
      sample_d0 <= in_sample_extended;
    end
  end
endmodule
