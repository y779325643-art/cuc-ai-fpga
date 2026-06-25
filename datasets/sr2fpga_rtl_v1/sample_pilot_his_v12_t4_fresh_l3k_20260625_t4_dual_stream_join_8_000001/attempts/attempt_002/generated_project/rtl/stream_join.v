// Joins two input streams: output valid when both inputs valid, output data = sum (mod 2^DATA_WIDTH)
`timescale 1ns / 1ps

/* verilator lint_off UNUSEDSIGNAL */
module stream_join #(
    parameter DATA_WIDTH = 8
) (
    input  wire                        clk,
    input  wire                        reset_n,
    input  wire [DATA_WIDTH-1:0]       in0_data,
    input  wire                        in0_valid,
    output wire                        in0_ready,
    input  wire [DATA_WIDTH-1:0]       in1_data,
    input  wire                        in1_valid,
    output wire                        in1_ready,
    output wire [DATA_WIDTH-1:0]       out_data,
    output wire                        out_valid,
    input  wire                        out_ready
);

    // No internal state; combinatorial logic
    assign in0_ready = out_ready;
    assign in1_ready = out_ready;
    assign out_valid = in0_valid && in1_valid;
    assign out_data  = in0_data + in1_data;

endmodule
/* verilator lint_on UNUSEDSIGNAL */
