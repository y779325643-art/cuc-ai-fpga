module stream_fork #(parameter DATA_WIDTH = 0) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out0_valid,
    output wire [DATA_WIDTH-1:0] out0_data,
    input wire out0_ready,
    output wire out1_valid,
    output wire [DATA_WIDTH-1:0] out1_data,
    input wire out1_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    assign in_ready = out0_ready & out1_ready;
    wire transfer = in_valid & in_ready;
    assign out0_valid = transfer;
    assign out1_valid = transfer;
    assign out0_data  = in_data;
    assign out1_data  = in_data;
endmodule
