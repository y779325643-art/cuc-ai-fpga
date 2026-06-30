module stream_join #(parameter DATA_WIDTH = 8) (
    input wire [None-1:0] clk,
    input wire [None-1:0] rst_n,
    input wire [None-1:0] in0_valid,
    input wire [DATA_WIDTH-1:0] in0_data,
    output wire [None-1:0] in0_ready,
    input wire [None-1:0] in1_valid,
    input wire [DATA_WIDTH-1:0] in1_data,
    output wire [None-1:0] in1_ready,
    output wire [None-1:0] out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire [None-1:0] out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    localparam WAIT_BOTH = 1'b0;
    wire _unused = WAIT_BOTH;

    assign out_valid = in0_valid && in1_valid;
    assign out_data  = in0_data;
    assign in0_ready = out_ready && in1_valid;
    assign in1_ready = out_ready && in0_valid;
endmodule
