module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [7:0] in_data,
    output wire in_ready,
    output wire out0_valid,
    output wire [7:0] out0_data,
    input wire out0_ready,
    output wire out1_valid,
    output wire [7:0] out1_data,
    input wire out1_ready
);
    wire skid_valid, skid_ready;
    wire [7:0] skid_data;
    wire fork0_valid, fork1_valid;
    wire [7:0] fork0_data, fork1_data;
    wire stage0_ready, stage1_ready;

    skid_buffer #(.WIDTH(8)) u_skid (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .in_ready(in_ready),
        .out_valid(skid_valid),
        .out_data(skid_data),
        .out_ready(skid_ready)
    );

    stream_fork #(.WIDTH(8)) u_fork (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(skid_valid),
        .in_data(skid_data),
        .in_ready(skid_ready),
        .out0_valid(fork0_valid),
        .out0_data(fork0_data),
        .out0_ready(stage0_ready),
        .out1_valid(fork1_valid),
        .out1_data(fork1_data),
        .out1_ready(stage1_ready)
    );

    stream_stage #(.WIDTH(8)) u_stage0 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(fork0_valid),
        .in_data(fork0_data),
        .in_ready(stage0_ready),
        .out_valid(out0_valid),
        .out_data(out0_data),
        .out_ready(out0_ready)
    );

    stream_stage #(.WIDTH(8)) u_stage1 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(fork1_valid),
        .in_data(fork1_data),
        .in_ready(stage1_ready),
        .out_valid(out1_valid),
        .out_data(out1_data),
        .out_ready(out1_ready)
    );
endmodule
