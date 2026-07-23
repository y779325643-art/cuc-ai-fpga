module threshold_comparator #(
    parameter ACC_WIDTH = 18,
    parameter THRESHOLD = 10
) (
    input wire in_valid,
    output wire in_ready,
    input wire signed [ACC_WIDTH-1:0] in_sample,
    input wire in_last,
    output wire out_valid,
    input wire out_ready,
    output wire signed [ACC_WIDTH-1:0] out_sample,
    output wire out_last
);

  wire signed [ACC_WIDTH-1:0] threshold_value;
  wire signed [ACC_WIDTH-1:0] one_value;
  wire signed [ACC_WIDTH-1:0] clamp_value;

  // The bounded positive default threshold makes THRESHOLD - 1 a safe rejected value.
  assign threshold_value = THRESHOLD;
  assign one_value = {{(ACC_WIDTH-1){1'b0}}, 1'b1};
  assign clamp_value = $signed(threshold_value) - $signed(one_value);
  assign in_ready = out_ready;
  assign out_valid = in_valid;
  assign out_sample = $signed(in_sample) >= $signed(threshold_value) ? in_sample : clamp_value;
  assign out_last = in_last;
endmodule
