`timescale 1ns / 1ps

module top (
    input  wire        clk,
    input  wire        nreset,
    input  wire        in_valid,
    input  wire [7:0]  in_data,
    output wire        in_ready,
    output wire        out0_valid,
    output wire [7:0]  out0_data,
    input  wire        out0_ready,
    output wire        out1_valid,
    output wire [7:0]  out1_data,
    input  wire        out1_ready
);

    // Internal connections
    wire        skid_out_valid;
    wire [7:0]  skid_out_data;
    wire        skid_out_ready;

    wire        fork_out0_valid;
    wire [7:0]  fork_out0_data;
    wire        fork_out0_ready;
    wire        fork_out1_valid;
    wire [7:0]  fork_out1_data;
    wire        fork_out1_ready;

    // Skid buffer
    skid_buffer #(
        .WIDTH(8)
    ) u_skid (
        .clk      (clk),
        .nreset   (nreset),
        .in_valid (in_valid),
        .in_data  (in_data),
        .in_ready (in_ready),
        .out_valid(skid_out_valid),
        .out_data (skid_out_data),
        .out_ready(skid_out_ready)
    );

    // Stream fork
    stream_fork #(
        .WIDTH(8)
    ) u_fork (
        .clk      (clk),
        .nreset   (nreset),
        .in_valid (skid_out_valid),
        .in_data  (skid_out_data),
        .in_ready (skid_out_ready),
        .out0_valid(fork_out0_valid),
        .out0_data (fork_out0_data),
        .out0_ready(fork_out0_ready),
        .out1_valid(fork_out1_valid),
        .out1_data (fork_out1_data),
        .out1_ready(fork_out1_ready)
    );

    // Output stage 0
    stream_stage #(
        .WIDTH(8)
    ) u_stage0 (
        .clk      (clk),
        .nreset   (nreset),
        .in_valid (fork_out0_valid),
        .in_data  (fork_out0_data),
        .in_ready (fork_out0_ready),
        .out_valid(out0_valid),
        .out_data (out0_data),
        .out_ready(out0_ready)
    );

    // Output stage 1
    stream_stage #(
        .WIDTH(8)
    ) u_stage1 (
        .clk      (clk),
        .nreset   (nreset),
        .in_valid (fork_out1_valid),
        .in_data  (fork_out1_data),
        .in_ready (fork_out1_ready),
        .out_valid(out1_valid),
        .out_data (out1_data),
        .out_ready(out1_ready)
    );

endmodule
