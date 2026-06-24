module top #(parameter WIDTH = 8) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] in0_data,
    input  wire in0_valid,
    output wire in0_ready,
    input  wire [WIDTH-1:0] in1_data,
    input  wire in1_valid,
    output wire in1_ready,
    input  wire clear,
    output wire [WIDTH-1:0] out_data,
    output wire out_valid,
    input  wire out_ready
);

    wire [WIDTH-1:0] in0_buffer_out_data;
    wire in0_buffer_out_valid;
    wire in0_buffer_out_ready;
    wire [WIDTH-1:0] in1_buffer_out_data;
    wire in1_buffer_out_valid;
    wire in1_buffer_out_ready;
    wire [WIDTH-1:0] join_out_data;
    wire join_out_valid;
    wire join_out_ready;
    wire [WIDTH-1:0] acc_out_data;
    wire acc_out_valid;
    wire acc_out_ready;

    skid_buffer #(
        .WIDTH(WIDTH),
        .DEPTH(2)
    ) in0_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .in_data(in0_data),
        .in_valid(in0_valid),
        .in_ready(in0_ready),
        .out_data(in0_buffer_out_data),
        .out_valid(in0_buffer_out_valid),
        .out_ready(in0_buffer_out_ready)
    );

    skid_buffer #(
        .WIDTH(WIDTH),
        .DEPTH(2)
    ) in1_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .in_data(in1_data),
        .in_valid(in1_valid),
        .in_ready(in1_ready),
        .out_data(in1_buffer_out_data),
        .out_valid(in1_buffer_out_valid),
        .out_ready(in1_buffer_out_ready)
    );

    stream_join #(
        .WIDTH(WIDTH)
    ) join_core (
        .clk(clk),
        .rst_n(rst_n),
        .in0_data(in0_buffer_out_data),
        .in0_valid(in0_buffer_out_valid),
        .in0_ready(in0_buffer_out_ready),
        .in1_data(in1_buffer_out_data),
        .in1_valid(in1_buffer_out_valid),
        .in1_ready(in1_buffer_out_ready),
        .out_data(join_out_data),
        .out_valid(join_out_valid),
        .out_ready(join_out_ready)
    );

    accumulator_core #(
        .WIDTH(WIDTH)
    ) accumulator (
        .clk(clk),
        .rst_n(rst_n),
        .in_data(join_out_data),
        .in_valid(join_out_valid),
        .in_ready(join_out_ready),
        .clear(clear),
        .out_data(acc_out_data),
        .out_valid(acc_out_valid),
        .out_ready(acc_out_ready)
    );

    stream_stage #(
        .WIDTH(WIDTH)
    ) out_stage (
        .clk(clk),
        .rst_n(rst_n),
        .in_data(acc_out_data),
        .in_valid(acc_out_valid),
        .in_ready(acc_out_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );

endmodule
