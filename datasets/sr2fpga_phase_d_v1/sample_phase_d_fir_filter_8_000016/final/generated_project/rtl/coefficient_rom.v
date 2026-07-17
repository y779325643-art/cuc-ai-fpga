module coefficient_rom #(parameter COEFF_WIDTH = 8, parameter NUM_TAPS = 3) (
    input wire clk,
    input wire rst_n,
    output wire [COEFF_WIDTH-1:0] coeff_0,
    output wire [COEFF_WIDTH-1:0] coeff_1,
    output wire [COEFF_WIDTH-1:0] coeff_2
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  assign coeff_0 = 8'd1;
  assign coeff_1 = 8'd2;
  assign coeff_2 = 8'd3;
  // SR2FPGA_BEHAVIOR_END
endmodule
