`timescale 1ns / 1ps

module top #(
    parameter DATA_WIDTH = 8
)(
    input  wire                clk,
    input  wire                reset_n,
    input  wire [DATA_WIDTH-1:0] in0_data,
    input  wire                in0_valid,
    output wire                in0_ready,
    input  wire [DATA_WIDTH-1:0] in1_data,
    input  wire                in1_valid,
    output wire                in1_ready,
    output wire [DATA_WIDTH-1:0] out_data,
    output wire                out_valid,
    input  wire                out_ready
);

    // Internal wires
    wire [DATA_WIDTH-1:0] buf0_out_data;
    wire buf0_out_valid;
    wire [DATA_WIDTH-1:0] buf1_out_data;
    wire buf1_out_valid;
    wire [DATA_WIDTH-1:0] join_out_data;
    wire join_out_valid;
    wire join_in0_ready, join_in1_ready;
    wire [DATA_WIDTH-1:0] acc_out_data;
    wire acc_out_valid;
    wire acc_in_ready;
    wire stage_in_ready;

    // Instantiations
    skid_buffer #(
        .DATA_WIDTH(DATA_WIDTH)
    ) in0_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .in_data(in0_data),
        .in_valid(in0_valid),
        .out_ready(join_in0_ready),
        .out_data(buf0_out_data),
        .out_valid(buf0_out_valid),
        .in_ready(in0_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(DATA_WIDTH)
    ) in1_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .in_data(in1_data),
        .in_valid(in1_valid),
        .out_ready(join_in1_ready),
        .out_data(buf1_out_data),
        .out_valid(buf1_out_valid),
        .in_ready(in1_ready)
    );

    stream_join #(
        .DATA_WIDTH(DATA_WIDTH)
    ) join_core (
        .clk(clk),
        .reset_n(reset_n),
        .in0_data(buf0_out_data),
        .in0_valid(buf0_out_valid),
        .in0_ready(join_in0_ready),
        .in1_data(buf1_out_data),
        .in1_valid(buf1_out_valid),
        .in1_ready(join_in1_ready),
        .out_data(join_out_data),
        .out_valid(join_out_valid),
        .out_ready(acc_in_ready)
    );

    accumulator_core #(
        .DATA_WIDTH(DATA_WIDTH)
    ) accumulator (
        .clk(clk),
        .reset_n(reset_n),
        .in_data(join_out_data),
        .in_valid(join_out_valid),
        .out_ready(stage_in_ready),
        .out_data(acc_out_data),
        .out_valid(acc_out_valid),
        .in_ready(acc_in_ready)
    );

    stream_stage #(
        .DATA_WIDTH(DATA_WIDTH)
    ) out_stage (
        .clk(clk),
        .reset_n(reset_n),
        .in_data(acc_out_data),
        .in_valid(acc_out_valid),
        .out_ready(out_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .in_ready(stage_in_ready)
    );

endmodule
