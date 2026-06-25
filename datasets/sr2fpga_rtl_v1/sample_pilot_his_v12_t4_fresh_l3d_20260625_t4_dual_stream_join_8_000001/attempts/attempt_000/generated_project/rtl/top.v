module top #(parameter DATA_WIDTH = 8) (
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] in0_data,
    input in0_valid,
    output in0_ready,
    input [DATA_WIDTH-1:0] in1_data,
    input in1_valid,
    output in1_ready,
    output [DATA_WIDTH-1:0] out_data,
    output out_valid,
    input out_ready
);

wire [DATA_WIDTH-1:0] buf0_out_data, buf1_out_data;
wire buf0_out_valid, buf1_out_valid;
wire join_in0_ready, join_in1_ready;
wire [DATA_WIDTH-1:0] join_out_data;
wire join_out_valid;
wire acc_in_ready;
wire [DATA_WIDTH-1:0] acc_out_data;
wire acc_out_valid;
wire stage_in_ready;

skid_buffer #(DATA_WIDTH) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in0_data),
    .in_valid(in0_valid),
    .in_ready(in0_ready),
    .out_data(buf0_out_data),
    .out_valid(buf0_out_valid),
    .out_ready(join_in0_ready)
);

skid_buffer #(DATA_WIDTH) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in1_data),
    .in_valid(in1_valid),
    .in_ready(in1_ready),
    .out_data(buf1_out_data),
    .out_valid(buf1_out_valid),
    .out_ready(join_in1_ready)
);

stream_join #(DATA_WIDTH) join_core (
    .clk(clk),
    .rst_n(rst_n),
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

accumulator_core #(DATA_WIDTH) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(join_out_data),
    .in_valid(join_out_valid),
    .in_ready(acc_in_ready),
    .out_data(acc_out_data),
    .out_valid(acc_out_valid),
    .out_ready(stage_in_ready)
);

stream_stage #(DATA_WIDTH) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(acc_out_data),
    .in_valid(acc_out_valid),
    .in_ready(stage_in_ready),
    .out_data(out_data),
    .out_valid(out_valid),
    .out_ready(out_ready)
);

endmodule
