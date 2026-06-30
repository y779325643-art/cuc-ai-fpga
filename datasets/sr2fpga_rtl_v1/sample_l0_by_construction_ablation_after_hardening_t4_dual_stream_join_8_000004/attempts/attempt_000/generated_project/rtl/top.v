// top.v: integration wrapper for the 8-bit dual-stream join datapath
module top (
    input clk,
    input rst_n,        // active low reset
    input [7:0] in0_data,
    input       in0_valid,
    output      in0_ready,
    input [7:0] in1_data,
    input       in1_valid,
    output      in1_ready,
    output [7:0] out_data,
    output      out_valid,
    input       out_ready
);

// internal wires
wire       s0_valid, s0_ready;
wire [7:0] s0_data;
wire       s1_valid, s1_ready;
wire [7:0] s1_data;
wire       join_valid, join_ready;
wire [7:0] join_data;
wire       acc_valid, acc_ready;
wire [7:0] acc_sum;

// skid buffers for input streams
skid_buffer u_skid0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_valid),
    .in_data(in0_data),
    .in_ready(in0_ready),
    .out_valid(s0_valid),
    .out_data(s0_data),
    .out_ready(s0_ready)
);

skid_buffer u_skid1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_valid),
    .in_data(in1_data),
    .in_ready(in1_ready),
    .out_valid(s1_valid),
    .out_data(s1_data),
    .out_ready(s1_ready)
);

// stream join: synchronizes and sums the two buffered streams
stream_join u_join (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(s0_valid),
    .in0_data(s0_data),
    .in0_ready(s0_ready),
    .in1_valid(s1_valid),
    .in1_data(s1_data),
    .in1_ready(s1_ready),
    .out_valid(join_valid),
    .out_data(join_data),
    .out_ready(join_ready)
);

// accumulator: accumulates joined values, outputs cumulative sum with handshake
accumulator_core u_acc (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(join_valid),
    .sample(join_data),
    .sample_ready(join_ready),
    .out_valid(acc_valid),
    .sum(acc_sum),
    .out_ready(acc_ready)
);

// stream_stage: final pipeline stage to register the output
stream_stage u_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(acc_valid),
    .in_data(acc_sum),
    .in_ready(acc_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(out_ready)
);

endmodule
