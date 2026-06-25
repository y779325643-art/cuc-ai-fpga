module top (
    input  wire        clk,
    input  wire        reset_n,
    input  wire        in0_valid,
    output wire        in0_ready,
    input  wire [7:0]  in0_data,
    input  wire        in1_valid,
    output wire        in1_ready,
    input  wire [7:0]  in1_data,
    output wire        out_valid,
    input  wire        out_ready,
    output wire [7:0]  out_data
);

    wire [7:0] buf0_out_data;
    wire       buf0_out_valid;
    wire       buf0_out_ready;
    wire [7:0] buf1_out_data;
    wire       buf1_out_valid;
    wire       buf1_out_ready;

    wire [7:0] join_out_data;
    wire       join_out_valid;
    wire       join_out_ready;

    wire [7:0] acc_out_data;
    wire       acc_out_valid;
    wire       acc_out_ready;

    skid_buffer #(
        .DATA_WIDTH(8)
    ) in0_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .in_valid(in0_valid),
        .in_ready(in0_ready),
        .in_data(in0_data),
        .out_valid(buf0_out_valid),
        .out_ready(buf0_out_ready),
        .out_data(buf0_out_data)
    );

    skid_buffer #(
        .DATA_WIDTH(8)
    ) in1_buffer (
        .clk(clk),
        .reset_n(reset_n),
        .in_valid(in1_valid),
        .in_ready(in1_ready),
        .in_data(in1_data),
        .out_valid(buf1_out_valid),
        .out_ready(buf1_out_ready),
        .out_data(buf1_out_data)
    );

    stream_join #(
        .DATA_WIDTH(8)
    ) join_core (
        .clk(clk),
        .reset_n(reset_n),
        .in0_valid(buf0_out_valid),
        .in0_ready(buf0_out_ready),
        .in0_data(buf0_out_data),
        .in1_valid(buf1_out_valid),
        .in1_ready(buf1_out_ready),
        .in1_data(buf1_out_data),
        .out_valid(join_out_valid),
        .out_ready(join_out_ready),
        .out_data(join_out_data)
    );

    accumulator_core #(
        .DATA_WIDTH(8)
    ) accumulator (
        .clk(clk),
        .reset_n(reset_n),
        .in_valid(join_out_valid),
        .in_ready(join_out_ready),
        .in_data(join_out_data),
        .out_valid(acc_out_valid),
        .out_ready(acc_out_ready),
        .out_data(acc_out_data)
    );

    stream_stage #(
        .DATA_WIDTH(8)
    ) out_stage (
        .clk(clk),
        .reset_n(reset_n),
        .in_valid(acc_out_valid),
        .in_ready(acc_out_ready),
        .in_data(acc_out_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_data(out_data)
    );

endmodule
