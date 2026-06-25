module top #(parameter DATA_WIDTH=8) (
    input clk, rst_n,
    input in0_valid, output in0_ready, input [DATA_WIDTH-1:0] in0_data,
    input in1_valid, output in1_ready, input [DATA_WIDTH-1:0] in1_data,
    output out_valid, input out_ready, output [DATA_WIDTH-1:0] out_data
);

wire [DATA_WIDTH-1:0] in0_buf_out_data, in1_buf_out_data;
wire in0_buf_out_valid, in0_buf_out_ready, in1_buf_out_valid, in1_buf_out_ready;
wire join_out_valid, join_out_ready;
wire [DATA_WIDTH-1:0] join_out_data;
wire acc_out_valid, acc_out_ready;
wire [DATA_WIDTH-1:0] acc_out_data;

skid_buffer #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(2)) in0_buffer (
    .clk(clk), .rst_n(rst_n),
    .in_valid(in0_valid), .in_ready(in0_ready), .in_data(in0_data),
    .out_valid(in0_buf_out_valid), .out_ready(in0_buf_out_ready), .out_data(in0_buf_out_data)
);

skid_buffer #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(2)) in1_buffer (
    .clk(clk), .rst_n(rst_n),
    .in_valid(in1_valid), .in_ready(in1_ready), .in_data(in1_data),
    .out_valid(in1_buf_out_valid), .out_ready(in1_buf_out_ready), .out_data(in1_buf_out_data)
);

stream_join #(.DATA_WIDTH(DATA_WIDTH)) join_core (
    .clk(clk), .rst_n(rst_n),
    .in0_valid(in0_buf_out_valid), .in0_ready(in0_buf_out_ready), .in0_data(in0_buf_out_data),
    .in1_valid(in1_buf_out_valid), .in1_ready(in1_buf_out_ready), .in1_data(in1_buf_out_data),
    .out_valid(join_out_valid), .out_ready(join_out_ready), .out_data(join_out_data)
);

accumulator_core #(.DATA_WIDTH(DATA_WIDTH)) accumulator (
    .clk(clk), .rst_n(rst_n),
    .in_valid(join_out_valid), .in_ready(join_out_ready), .in_data(join_out_data),
    .out_valid(acc_out_valid), .out_ready(acc_out_ready), .out_data(acc_out_data)
);

stream_stage #(.DATA_WIDTH(DATA_WIDTH)) out_stage (
    .clk(clk), .rst_n(rst_n),
    .in_valid(acc_out_valid), .in_ready(acc_out_ready), .in_data(acc_out_data),
    .out_valid(out_valid), .out_ready(out_ready), .out_data(out_data)
);

endmodule
