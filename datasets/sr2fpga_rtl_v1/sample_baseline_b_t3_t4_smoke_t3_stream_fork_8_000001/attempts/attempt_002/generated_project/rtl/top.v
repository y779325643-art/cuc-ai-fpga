module top (
    input clk,
    input rst_n,
    input [7:0] in_data,
    input in_valid,
    output in_ready,
    output [7:0] out0_data,
    output out0_valid,
    input out0_ready,
    output [7:0] out1_data,
    output out1_valid,
    input out1_ready
);

wire [7:0] skid_out_data;
wire skid_out_valid, skid_out_ready;
wire fork_in_ready;
wire [7:0] fork_out0_data, fork_out1_data;
wire fork_out0_valid, fork_out0_ready;
wire fork_out1_valid, fork_out1_ready;

skid_buffer #(.WIDTH(8)) skid (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in_data),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .out_data(skid_out_data),
    .out_valid(skid_out_valid),
    .out_ready(skid_out_ready)
);

stream_fork #(.WIDTH(8)) fork_inst (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(skid_out_data),
    .in_valid(skid_out_valid),
    .in_ready(skid_out_ready),
    .out0_data(fork_out0_data),
    .out0_valid(fork_out0_valid),
    .out0_ready(fork_out0_ready),
    .out1_data(fork_out1_data),
    .out1_valid(fork_out1_valid),
    .out1_ready(fork_out1_ready)
);

stream_stage #(.WIDTH(8)) stage0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(fork_out0_data),
    .in_valid(fork_out0_valid),
    .in_ready(fork_out0_ready),
    .out_data(out0_data),
    .out_valid(out0_valid),
    .out_ready(out0_ready)
);

stream_stage #(.WIDTH(8)) stage1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(fork_out1_data),
    .in_valid(fork_out1_valid),
    .in_ready(fork_out1_ready),
    .out_data(out1_data),
    .out_valid(out1_valid),
    .out_ready(out1_ready)
);

endmodule
