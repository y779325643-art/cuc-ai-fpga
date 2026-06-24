module top (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       in0_valid,
    input  wire [7:0] in0_data,
    output wire       in0_ready,
    input  wire       in1_valid,
    input  wire [7:0] in1_data,
    output wire       in1_ready,
    output wire       out_valid,
    output wire [15:0] out_data,
    input  wire       out_ready
);

    wire buff_in0_valid, buff_in0_ready;
    wire [7:0] buff_in0_data;
    wire buff_in1_valid, buff_in1_ready;
    wire [7:0] buff_in1_data;
    wire join_valid, join_ready;
    wire [7:0] join_data;
    wire accum_valid, accum_ready;
    wire [15:0] accum_data;

    skid_buffer #(
        .DATA_WIDTH(8)
    ) in0_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in0_valid),
        .in_data(in0_data),
        .in_ready(in0_ready),
        .out_valid(buff_in0_valid),
        .out_data(buff_in0_data),
        .out_ready(buff_in0_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(8)
    ) in1_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in1_valid),
        .in_data(in1_data),
        .in_ready(in1_ready),
        .out_valid(buff_in1_valid),
        .out_data(buff_in1_data),
        .out_ready(buff_in1_ready)
    );

    stream_join #(
        .DATA_WIDTH(8)
    ) join (
        .clk(clk),
        .rst_n(rst_n),
        .in0_valid(buff_in0_valid),
        .in0_data(buff_in0_data),
        .in0_ready(buff_in0_ready),
        .in1_valid(buff_in1_valid),
        .in1_data(buff_in1_data),
        .in1_ready(buff_in1_ready),
        .out_valid(join_valid),
        .out_data(join_data),
        .out_ready(join_ready)
    );

    accumulator_core #(
        .DATA_WIDTH(8),
        .ACCUM_WIDTH(16)
    ) accumulator (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(join_valid),
        .in_data(join_data),
        .in_ready(join_ready),
        .out_valid(accum_valid),
        .out_data(accum_data),
        .out_ready(accum_ready)
    );

    stream_stage #(
        .DATA_WIDTH(16)
    ) out_stage (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(accum_valid),
        .in_data(accum_data),
        .in_ready(accum_ready),
        .out_valid(out_valid),
        .out_data(out_data),
        .out_ready(out_ready)
    );

endmodule
