module peak_detector_core #(
    parameter WIDTH = 18,
    parameter THRESHOLD = 10
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire signed [WIDTH-1:0] in_sample,
    input wire in_last,
    output reg out_valid,
    input wire out_ready,
    output reg out_peak_found,
    output reg signed [WIDTH-1:0] out_peak_value,
    output reg [WIDTH-1:0] out_peak_index
);

  reg peak_found;
  reg signed [WIDTH-1:0] peak_value;
  reg [WIDTH-1:0] peak_index;
  reg [WIDTH-1:0] sample_index;
  wire sample_qualifies;
  wire signed [WIDTH-1:0] candidate_value;
  wire candidate_is_new_peak;
  wire candidate_found;
  wire [WIDTH-1:0] candidate_index;

  assign in_ready = !out_valid || out_ready;
  assign sample_qualifies = $signed(in_sample) >= THRESHOLD;
  assign candidate_value = in_sample;
  assign candidate_is_new_peak = sample_qualifies && (!peak_found || candidate_value > peak_value);
  assign candidate_found = peak_found || sample_qualifies;
  assign candidate_index = candidate_is_new_peak ? sample_index : peak_index;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      peak_found <= 1'b0;
      peak_value <= {WIDTH{1'b0}};
      peak_index <= {WIDTH{1'b0}};
      sample_index <= {WIDTH{1'b0}};
      out_valid <= 1'b0;
      out_peak_found <= 1'b0;
      out_peak_value <= {WIDTH{1'b0}};
      out_peak_index <= {WIDTH{1'b0}};
    end else if (in_ready) begin
      out_valid <= 1'b0;
      if (in_valid) begin
        if (in_last) begin
          out_valid <= 1'b1;
          out_peak_found <= candidate_found;
          out_peak_value <= candidate_found ? peak_value : {WIDTH{1'b0}};
          out_peak_index <= candidate_found ? candidate_index : {WIDTH{1'b0}};
          peak_found <= 1'b0;
          peak_value <= {WIDTH{1'b0}};
          peak_index <= {WIDTH{1'b0}};
          sample_index <= {WIDTH{1'b0}};
        end else begin
          peak_found <= candidate_found;
          if (candidate_is_new_peak) begin
            peak_value <= candidate_value;
            peak_index <= sample_index;
          end
          sample_index <= sample_index + 1'b1;
        end
      end
    end
  end
endmodule
