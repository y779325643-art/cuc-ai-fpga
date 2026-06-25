`timescale 1ns / 1ps
module top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_valid,
    output wire        in_ready,
    input  wire [7:0]  in_data,
    output wire        out_valid,
    input  wire        out_ready,
    output wire [7:0]  out_data
);

    wire [7:0] buffered_data;
    wire        buffered_valid;
    wire        buffered_ready;

    skid_buffer #(
        .DATA_WIDTH(8)
    ) input_buffer (
        .clk      (clk),
        .rst_n    (rst_n),
        .in_valid (in_valid),
        .in_ready (in_ready),
        .in_data  (in_data),
        .out_valid(buffered_valid),
        .out_ready(buffered_ready),
        .out_data (buffered_data)
    );

    accumulator_core #(
        .DATA_WIDTH(8)
    ) accumulator (
        .clk      (clk),
        .rst_n    (rst_n),
        .in_valid (buffered_valid),
        .in_ready (buffered_ready),
        .in_data  (buffered_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_data (out_data)
    );

endmodule
