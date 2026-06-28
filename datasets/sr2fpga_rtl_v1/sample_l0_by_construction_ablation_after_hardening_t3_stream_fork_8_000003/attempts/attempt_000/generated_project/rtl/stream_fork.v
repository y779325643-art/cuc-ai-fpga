`timescale 1ns / 1ps

module stream_fork #(
    parameter WIDTH = 8
) (
    input  wire        clk,
    input  wire        nreset,
    input  wire        in_valid,
    input  wire [WIDTH-1:0] in_data,
    output wire        in_ready,
    output wire        out0_valid,
    output wire [WIDTH-1:0] out0_data,
    input  wire        out0_ready,
    output wire        out1_valid,
    output wire [WIDTH-1:0] out1_data,
    input  wire        out1_ready
);

    // Fork only proceeds when both outputs are ready
    assign in_ready = out0_ready & out1_ready;

    // Valid outputs are active only when both sides are ready and input is valid
    wire fork_enable = in_valid & out0_ready & out1_ready;
    assign out0_valid = fork_enable;
    assign out1_valid = fork_enable;

    // Data duplication
    assign out0_data = in_data;
    assign out1_data = in_data;

endmodule
