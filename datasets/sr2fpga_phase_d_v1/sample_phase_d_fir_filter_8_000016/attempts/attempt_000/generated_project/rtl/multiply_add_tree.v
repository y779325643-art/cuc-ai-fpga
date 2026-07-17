module multiply_add_tree #(parameter DATA_WIDTH = 8, parameter COEFF_WIDTH = 8, parameter NUM_TAPS = 3, parameter OUTPUT_WIDTH = 16) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] data_0,
    input wire [DATA_WIDTH-1:0] data_1,
    input wire [DATA_WIDTH-1:0] data_2,
    input wire [COEFF_WIDTH-1:0] coeff_0,
    input wire [COEFF_WIDTH-1:0] coeff_1,
    input wire [COEFF_WIDTH-1:0] coeff_2,
    output wire [OUTPUT_WIDTH-1:0] result
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  wire signed [15:0] prod0 = $signed(data_0) * $signed(coeff_0);
  wire signed [15:0] prod1 = $signed(data_1) * $signed(coeff_1);
  wire signed [15:0] prod2 = $signed(data_2) * $signed(coeff_2);
  wire signed [17:0] sum = prod0 + prod1 + prod2;
  assign result = sum[OUTPUT_WIDTH-1:0];
  wire _unused_mac = |sum;
  // SR2FPGA_BEHAVIOR_END
endmodule
