// top module: integration wrapper for dual-stream join with accumulation
`timescale 1ns / 1ps

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
    parameter DATA_WIDTH = 8;

    // Internal wires
    wire [DATA_WIDTH-1:0] in0_buf_data;
    wire                  in0_buf_valid;
    wire                  in0_buf_ready;
    wire [DATA_WIDTH-1:0] in1_buf_data;
    wire                  in1_buf_valid;
    wire                  in1_buf_ready;
    wire [DATA_WIDTH-1:0] join_data;
    wire                  join_valid;
    wire                  join_ready;
    wire [DATA_WIDTH-1:0] accum_data;
    wire                  accum_valid;
    wire                  accum_ready;
    wire [DATA_WIDTH-1:0] out_stage_data;
    wire                  out_stage_valid;
    wire                  out_stage_ready;

    // Instances
    skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in0_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .s_in_data(in0_data),
        .s_in_valid(in0_valid),
        .s_in_ready(in0_ready),
        .s_out_data(in0_buf_data),
        .s_out_valid(in0_buf_valid),
        .s_out_ready(in0_buf_ready)
    );

    skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in1_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .s_in_data(in1_data),
        .s_in_valid(in1_valid),
        .s_in_ready(in1_ready),
        .s_out_data(in1_buf_data),
        .s_out_valid(in1_buf_valid),
        .s_out_ready(in1_buf_ready)
    );

    stream_join #(.DATA_WIDTH(DATA_WIDTH)) join_core (
        .clk(clk),
        .reset_n(reset_n),
        .in0_data(in0_buf_data),
        .in0_valid(in0_buf_valid),
        .in0_ready(in0_buf_ready),
        .in1_data(in1_buf_data),
        .in1_valid(in1_buf_valid),
        .in1_ready(in1_buf_ready),
        .out_data(join_data),
        .out_valid(join_valid),
        .out_ready(join_ready)
    );

    accumulator_core #(.DATA_WIDTH(DATA_WIDTH)) accumulator (
        .clk(clk),
        .reset_n(reset_n),
        .data_in(join_data),
        .valid_in(join_valid),
        .ready_out(join_ready),
        .data_out(accum_data),
        .valid_out(accum_valid),
        .ready_in(accum_ready)
    );

    stream_stage #(.DATA_WIDTH(DATA_WIDTH)) out_stage (
        .clk(clk),
        .reset_n(reset_n),
        .s_in_data(accum_data),
        .s_in_valid(accum_valid),
        .s_in_ready(accum_ready),
        .s_out_data(out_stage_data),
        .s_out_valid(out_stage_valid),
        .s_out_ready(out_stage_ready)
    );

    // Output assignments
    assign out_data        = out_stage_data;
    assign out_valid       = out_stage_valid;
    assign out_stage_ready = out_ready;

endmodule
