module stream_join #(parameter WIDTH_A = 8, parameter WIDTH_B = 8, parameter OUTPUT_WIDTH = 16) (
    input wire clk,
    input wire rst_n,
    input wire a_valid,
    input wire [WIDTH_A-1:0] a_data,
    output wire a_ready,
    input wire b_valid,
    input wire [WIDTH_B-1:0] b_data,
    output wire b_ready,
    output wire out_valid,
    output wire [OUTPUT_WIDTH-1:0] out_data,
    input wire out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    wire both_valid = a_valid && b_valid;
    wire [WIDTH_A-1:0] extended_a = a_data;
    wire [WIDTH_B-1:0] extended_b = b_data;
    wire [OUTPUT_WIDTH-1:0] joined_result = extended_a + extended_b;

    assign a_ready = out_ready && b_valid;
    assign b_ready = out_ready && a_valid;
    assign out_valid = both_valid;
    assign out_data = joined_result;
  // SR2FPGA_BEHAVIOR_END
endmodule
