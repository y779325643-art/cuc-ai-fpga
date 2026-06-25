// top.v - Integration wrapper for dual-stream join with accumulation
// System-HIS v1.2 contract
`timescale 1ns/1ps

module top (
    input  wire        clk,
    input  wire        reset_n,
    input  wire [7:0]  in0_data,
    input  wire        in0_valid,
    output wire        in0_ready,
    input  wire [7:0]  in1_data,
    input  wire        in1_valid,
    output wire        in1_ready,
    output wire [7:0]  out_data,
    output wire        out_valid,
    input  wire        out_ready
);

    // Internal wires
    wire [7:0] in0_buffer_data_out;
    wire       in0_buffer_valid_out;
    wire       in0_buffer_ready_out;
    wire [7:0] in1_buffer_data_out;
    wire       in1_buffer_valid_out;
    wire       in1_buffer_ready_out;
    wire [7:0] join_core_out_data;
    wire       join_core_out_valid;
    wire       join_core_out_ready;
    wire [7:0] accumulator_out_data;
    wire       accumulator_out_valid;
    wire       accumulator_out_ready;

    // Instance in0_buffer
    skid_buffer #(
        .DATA_WIDTH(8),
        .DEPTH(2)
    ) in0_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .data_in(in0_data),
        .valid_in(in0_valid),
        .ready_out(in0_ready),
        .data_out(in0_buffer_data_out),
        .valid_out(in0_buffer_valid_out),
        .ready_in(in0_buffer_ready_out)
    );

    // Instance in1_buffer
    skid_buffer #(
        .DATA_WIDTH(8),
        .DEPTH(2)
    ) in1_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .data_in(in1_data),
        .valid_in(in1_valid),
        .ready_out(in1_ready),
        .data_out(in1_buffer_data_out),
        .valid_out(in1_buffer_valid_out),
        .ready_in(in1_buffer_ready_out)
    );

    // Instance join_core
    stream_join #(
        .DATA_WIDTH(8)
    ) join_core (
        .clk(clk),
        .reset_n(reset_n),
        .in0_data(in0_buffer_data_out),
        .in0_valid(in0_buffer_valid_out),
        .in0_ready(in0_buffer_ready_out),
        .in1_data(in1_buffer_data_out),
        .in1_valid(in1_buffer_valid_out),
        .in1_ready(in1_buffer_ready_out),
        .out_data(join_core_out_data),
        .out_valid(join_core_out_valid),
        .out_ready(join_core_out_ready)
    );

    // Instance accumulator
    accumulator_core #(
        .DATA_WIDTH(8)
    ) accumulator (
        .clk(clk),
        .reset_n(reset_n),
        .in_data(join_core_out_data),
        .in_valid(join_core_out_valid),
        .in_ready(join_core_out_ready),
        .out_data(accumulator_out_data),
        .out_valid(accumulator_out_valid),
        .out_ready(accumulator_out_ready)
    );

    // Instance out_stage
    stream_stage #(
        .DATA_WIDTH(8)
    ) out_stage (
        .clk(clk),
        .reset_n(reset_n),
        .in_data(accumulator_out_data),
        .in_valid(accumulator_out_valid),
        .in_ready(accumulator_out_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );

endmodule
