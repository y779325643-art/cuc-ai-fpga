`timescale 1ns/1ns
module top (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [7:0] in0_data,
    input wire in1_valid,
    input wire [7:0] in1_data,
    output wire out_valid,
    output wire [15:0] out_data,
    output wire in0_ready,
    output wire in1_ready
);

wire sb0_out_valid, sb0_out_ready;
wire [7:0] sb0_out_data;
wire sb1_out_valid, sb1_out_ready;
wire [7:0] sb1_out_data;

wire join_out_valid, join_out_ready;
wire [15:0] join_out_data;

wire acc_out_valid, acc_out_ready;
wire [15:0] acc_out_data;

skid_buffer #(.DATA_WIDTH(8)) sb0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_valid),
    .in_data(in0_data),
    .out_ready(sb0_out_ready),
    .out_valid(sb0_out_valid),
    .out_data(sb0_out_data),
    .in_ready(in0_ready)
);

skid_buffer #(.DATA_WIDTH(8)) sb1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_valid),
    .in_data(in1_data),
    .out_ready(sb1_out_ready),
    .out_valid(sb1_out_valid),
    .out_data(sb1_out_data),
    .in_ready(in1_ready)
);

stream_join #(.DATA_WIDTH(8)) join (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(sb0_out_valid),
    .in0_data(sb0_out_data),
    .in0_ready(sb0_out_ready),
    .in1_valid(sb1_out_valid),
    .in1_data(sb1_out_data),
    .in1_ready(sb1_out_ready),
    .out_valid(join_out_valid),
    .out_data(join_out_data),
    .out_ready(join_out_ready)
);

accumulator_core #(.DATA_WIDTH(8), .SUM_WIDTH(16)) acc (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(join_out_valid),
    .sample(join_out_data),
    .sample_ready(join_out_ready),
    .sum_valid(acc_out_valid),
    .sum(acc_out_data),
    .sum_ready(acc_out_ready)
);

stream_stage #(.DATA_WIDTH(16)) stg (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(acc_out_valid),
    .in_data(acc_out_data),
    .in_ready(acc_out_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(1'b1) // always ready in test
);

endmodule
