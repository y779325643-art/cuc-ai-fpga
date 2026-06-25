module top (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [7:0] in0_data,
    input wire in1_valid,
    input wire [7:0] in1_data,
    output wire in0_ready,
    output wire in1_ready,
    output wire out_valid,
    output wire [7:0] out_data,
    input wire out_ready
);

wire skid0_out_valid, skid1_out_valid;
wire [7:0] skid0_out_data, skid1_out_data;
wire skid0_out_ready, skid1_out_ready;
wire join_out_valid;
wire [7:0] join_out_data;
wire join_out_ready;
wire acc_sample_valid;
wire [7:0] acc_sample;
wire acc_sample_ready;
wire acc_out_valid;
wire [7:0] acc_out_data;
wire acc_out_ready;

skid_buffer #(.WIDTH(8)) u_skid0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_valid),
    .in_data(in0_data),
    .in_ready(in0_ready),
    .out_valid(skid0_out_valid),
    .out_data(skid0_out_data),
    .out_ready(skid0_out_ready)
);

skid_buffer #(.WIDTH(8)) u_skid1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_valid),
    .in_data(in1_data),
    .in_ready(in1_ready),
    .out_valid(skid1_out_valid),
    .out_data(skid1_out_data),
    .out_ready(skid1_out_ready)
);

stream_join #(.WIDTH(8)) u_join (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(skid0_out_valid),
    .in0_data(skid0_out_data),
    .in0_ready(skid0_out_ready),
    .in1_valid(skid1_out_valid),
    .in1_data(skid1_out_data),
    .in1_ready(skid1_out_ready),
    .out_valid(join_out_valid),
    .out_data(join_out_data),
    .out_ready(join_out_ready)
);

accumulator_core #(.WIDTH(8)) u_acc (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(join_out_valid),
    .sample(join_out_data),
    .sample_ready(join_out_ready),
    .out_valid(acc_out_valid),
    .out_data(acc_out_data),
    .out_ready(acc_out_ready)
);

stream_stage #(.WIDTH(8)) u_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(acc_out_valid),
    .in_data(acc_out_data),
    .in_ready(acc_out_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(out_ready)
);

endmodule
