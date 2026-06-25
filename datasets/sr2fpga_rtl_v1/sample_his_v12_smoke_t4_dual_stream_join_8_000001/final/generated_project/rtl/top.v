module top (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] in0_data,
    input  wire       in0_valid,
    output wire       in0_ready,
    input  wire [7:0] in1_data,
    input  wire       in1_valid,
    output wire       in1_ready,
    output wire [7:0] out_data,
    output wire       out_valid,
    input  wire       out_ready
);

wire [7:0] buf0_data_out;
wire       buf0_valid_out;
wire       buf0_ready_in;
wire [7:0] buf1_data_out;
wire       buf1_valid_out;
wire       buf1_ready_in;
wire [7:0] join_data_out;
wire       join_valid_out;
wire       join_ready_in;
wire [7:0] accum_data_out;
wire       accum_valid_out;
wire       accum_ready_in;
wire [7:0] stage_data_out;
wire       stage_valid_out;
wire       stage_ready_in;

skid_buffer #(
    .DATA_WIDTH(8)
) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .data_in(in0_data),
    .valid_in(in0_valid),
    .ready_out(in0_ready),
    .data_out(buf0_data_out),
    .valid_out(buf0_valid_out),
    .ready_in(buf0_ready_in)
);

skid_buffer #(
    .DATA_WIDTH(8)
) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .data_in(in1_data),
    .valid_in(in1_valid),
    .ready_out(in1_ready),
    .data_out(buf1_data_out),
    .valid_out(buf1_valid_out),
    .ready_in(buf1_ready_in)
);

stream_join #(
    .DATA_WIDTH(8)
) join (
    .clk(clk),
    .rst_n(rst_n),
    .data_in0(buf0_data_out),
    .valid_in0(buf0_valid_out),
    .ready_out0(buf0_ready_in),
    .data_in1(buf1_data_out),
    .valid_in1(buf1_valid_out),
    .ready_out1(buf1_ready_in),
    .data_out(join_data_out),
    .valid_out(join_valid_out),
    .ready_in(join_ready_in)
);

accumulator_core #(
    .DATA_WIDTH(8)
) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .data_in(join_data_out),
    .valid_in(join_valid_out),
    .ready_out(join_ready_in),
    .data_out(accum_data_out),
    .valid_out(accum_valid_out),
    .ready_in(accum_ready_in)
);

stream_stage #(
    .DATA_WIDTH(8)
) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .data_in(accum_data_out),
    .valid_in(accum_valid_out),
    .ready_out(accum_ready_in),
    .data_out(stage_data_out),
    .valid_out(stage_valid_out),
    .ready_in(stage_ready_in)
);

assign out_data = stage_data_out;
assign out_valid = stage_valid_out;
assign stage_ready_in = out_ready;

endmodule
