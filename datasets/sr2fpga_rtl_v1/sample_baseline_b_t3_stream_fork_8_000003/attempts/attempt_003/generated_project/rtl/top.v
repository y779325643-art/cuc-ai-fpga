module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    output wire out0_valid,
    input wire out0_ready,
    output wire [7:0] out0_data,
    output wire out1_valid,
    input wire out1_ready,
    output wire [7:0] out1_data
);

    wire skid_valid, skid_ready;
    wire [7:0] skid_data;
    wire fork_out0_valid, fork_out0_ready;
    wire [7:0] fork_out0_data;
    wire fork_out1_valid, fork_out1_ready;
    wire [7:0] fork_out1_data;

    skid_buffer #(.WIDTH(8)) u_skid (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_data(in_data),
        .out_valid(skid_valid),
        .out_ready(skid_ready),
        .out_data(skid_data)
    );

    stream_fork #(.WIDTH(8)) u_fork (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(skid_valid),
        .in_ready(skid_ready),
        .in_data(skid_data),
        .out0_valid(fork_out0_valid),
        .out0_ready(fork_out0_ready),
        .out0_data(fork_out0_data),
        .out1_valid(fork_out1_valid),
        .out1_ready(fork_out1_ready),
        .out1_data(fork_out1_data)
    );

    stream_stage #(.WIDTH(8)) u_stage0 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(fork_out0_valid),
        .in_ready(fork_out0_ready),
        .in_data(fork_out0_data),
        .out_valid(out0_valid),
        .out_ready(out0_ready),
        .out_data(out0_data)
    );

    stream_stage #(.WIDTH(8)) u_stage1 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(fork_out1_valid),
        .in_ready(fork_out1_ready),
        .in_data(fork_out1_data),
        .out_valid(out1_valid),
        .out_ready(out1_ready),
        .out_data(out1_data)
    );

endmodule
