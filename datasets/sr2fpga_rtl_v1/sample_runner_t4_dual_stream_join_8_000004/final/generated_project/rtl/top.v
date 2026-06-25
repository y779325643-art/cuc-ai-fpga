module top (
    input clk,
    input rst_n,
    input in0_valid,
    input [7:0] in0_data,
    output in0_ready,
    input in1_valid,
    input [7:0] in1_data,
    output in1_ready,
    output out_valid,
    output [7:0] out_data,
    input out_ready
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
    wire acc_sum_valid;
    wire [7:0] acc_sum;
    wire acc_sum_ready;
    
    skid_buffer #(8) skid0 (
        .clk(clk), .rst_n(rst_n),
        .in_valid(in0_valid), .in_data(in0_data), .in_ready(in0_ready),
        .out_valid(skid0_out_valid), .out_data(skid0_out_data), .out_ready(skid0_out_ready)
    );
    skid_buffer #(8) skid1 (
        .clk(clk), .rst_n(rst_n),
        .in_valid(in1_valid), .in_data(in1_data), .in_ready(in1_ready),
        .out_valid(skid1_out_valid), .out_data(skid1_out_data), .out_ready(skid1_out_ready)
    );
    stream_join #(8) join_inst (
        .clk(clk), .rst_n(rst_n),
        .in0_valid(skid0_out_valid), .in0_data(skid0_out_data), .in0_ready(skid0_out_ready),
        .in1_valid(skid1_out_valid), .in1_data(skid1_out_data), .in1_ready(skid1_out_ready),
        .out_valid(join_out_valid), .out_data(join_out_data), .out_ready(join_out_ready)
    );
    accumulator_core #(8) acc_inst (
        .clk(clk), .rst_n(rst_n),
        .sample_valid(join_out_valid), .sample(join_out_data), .sample_ready(join_out_ready),
        .sum_valid(acc_sum_valid), .sum(acc_sum), .sum_ready(acc_sum_ready)
    );
    stream_stage #(8) stage_inst (
        .clk(clk), .rst_n(rst_n),
        .in_valid(acc_sum_valid), .in_data(acc_sum), .in_ready(acc_sum_ready),
        .out_valid(out_valid), .out_data(out_data), .out_ready(out_ready)
    );
endmodule
