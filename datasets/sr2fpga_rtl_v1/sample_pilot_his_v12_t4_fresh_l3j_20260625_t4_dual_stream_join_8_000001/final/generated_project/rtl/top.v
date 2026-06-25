module top #(
    parameter DATA_WIDTH = 8
)(
    input  wire clk,
    input  wire rst_n,
    input  wire in0_valid,
    output wire in0_ready,
    input  wire [DATA_WIDTH-1:0] in0_data,
    input  wire in1_valid,
    output wire in1_ready,
    input  wire [DATA_WIDTH-1:0] in1_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);

    wire [DATA_WIDTH-1:0] in0_buf_data;
    wire in0_buf_valid;
    wire in0_buf_ready;
    wire [DATA_WIDTH-1:0] in1_buf_data;
    wire in1_buf_valid;
    wire in1_buf_ready;

    wire [DATA_WIDTH-1:0] join_data;
    wire join_valid;
    wire join_ready;

    wire [DATA_WIDTH-1:0] acc_data;
    wire acc_valid;
    wire acc_ready;

    // Input skid buffers
    skid_buffer #(
        .DATA_WIDTH(DATA_WIDTH)
    ) in0_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(in0_valid),
        .ready_in(in0_ready),
        .data_in(in0_data),
        .valid_out(in0_buf_valid),
        .ready_out(in0_buf_ready),
        .data_out(in0_buf_data)
    );

    skid_buffer #(
        .DATA_WIDTH(DATA_WIDTH)
    ) in1_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(in1_valid),
        .ready_in(in1_ready),
        .data_in(in1_data),
        .valid_out(in1_buf_valid),
        .ready_out(in1_buf_ready),
        .data_out(in1_buf_data)
    );

    // Stream join
    stream_join #(
        .DATA_WIDTH(DATA_WIDTH)
    ) join_core (
        .clk(clk),
        .rst_n(rst_n),
        .in0_valid(in0_buf_valid),
        .in0_ready(in0_buf_ready),
        .in0_data(in0_buf_data),
        .in1_valid(in1_buf_valid),
        .in1_ready(in1_buf_ready),
        .in1_data(in1_buf_data),
        .out_valid(join_valid),
        .out_ready(join_ready),
        .out_data(join_data)
    );

    // Accumulator
    accumulator_core #(
        .DATA_WIDTH(DATA_WIDTH)
    ) accumulator (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(join_valid),
        .ready_in(join_ready),
        .data_in(join_data),
        .valid_out(acc_valid),
        .ready_out(acc_ready),
        .data_out(acc_data)
    );

    // Output pipeline stage
    stream_stage #(
        .DATA_WIDTH(DATA_WIDTH)
    ) out_stage (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(acc_valid),
        .ready_in(acc_ready),
        .data_in(acc_data),
        .valid_out(out_valid),
        .ready_out(out_ready),
        .data_out(out_data)
    );

endmodule
