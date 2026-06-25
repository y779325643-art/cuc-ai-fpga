// top module: dual-stream join with accumulation
// Generated from System-HIS v1.2

`default_nettype none

module top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [DATA_WIDTH-1:0]  in0_data,
    input  wire        in0_valid,
    output wire        in0_ready,
    input  wire [DATA_WIDTH-1:0]  in1_data,
    input  wire        in1_valid,
    output wire        in1_ready,
    output wire [DATA_WIDTH-1:0]  out_data,
    output wire        out_valid,
    input  wire        out_ready
);

    parameter DATA_WIDTH = 8;

    // wires between instances
    wire [DATA_WIDTH-1:0] in0_buf_data;
    wire                  in0_buf_valid;
    wire                  in0_buf_ready;
    wire [DATA_WIDTH-1:0] in1_buf_data;
    wire                  in1_buf_valid;
    wire                  in1_buf_ready;
    wire [DATA_WIDTH-1:0] join_data;
    wire                  join_valid;
    wire                  join_ready;
    wire [DATA_WIDTH-1:0] accum_data;
    wire                  accum_valid;
    wire                  accum_ready;
    wire [DATA_WIDTH-1:0] stage_data;
    wire                  stage_valid;
    wire                  stage_ready;
    wire                  join_core_ready0;
    wire                  join_core_ready1;

    // Instantiate in0_buffer (skid_buffer)
    skid_buffer #(
        .DATA_WIDTH(DATA_WIDTH)
    ) in0_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(in0_data),
        .valid_in(in0_valid),
        .ready_out(in0_ready),
        .data_out(in0_buf_data),
        .valid_out(in0_buf_valid),
        .ready_in(join_core_ready0)
    );

    // Instantiate in1_buffer (skid_buffer)
    skid_buffer #(
        .DATA_WIDTH(DATA_WIDTH)
    ) in1_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(in1_data),
        .valid_in(in1_valid),
        .ready_out(in1_ready),
        .data_out(in1_buf_data),
        .valid_out(in1_buf_valid),
        .ready_in(join_core_ready1)
    );

    // Instantiate join_core (stream_join)
    stream_join #(
        .DATA_WIDTH(DATA_WIDTH)
    ) join_core (
        .clk(clk),
        .rst_n(rst_n),
        .data_in0(in0_buf_data),
        .valid_in0(in0_buf_valid),
        .ready_out0(join_core_ready0),
        .data_in1(in1_buf_data),
        .valid_in1(in1_buf_valid),
        .ready_out1(join_core_ready1),
        .data_out(join_data),
        .valid_out(join_valid),
        .ready_in(join_ready)
    );

    // Instantiate accumulator (accumulator_core)
    accumulator_core #(
        .DATA_WIDTH(DATA_WIDTH)
    ) accumulator (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(join_data),
        .valid_in(join_valid),
        .ready_out(join_ready),
        .data_out(accum_data),
        .valid_out(accum_valid),
        .ready_in(accum_ready)
    );

    // Instantiate out_stage (stream_stage)
    stream_stage #(
        .DATA_WIDTH(DATA_WIDTH)
    ) out_stage (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(accum_data),
        .valid_in(accum_valid),
        .ready_out(accum_ready),
        .data_out(out_data),
        .valid_out(out_valid),
        .ready_in(out_ready)
    );

endmodule

`default_nettype wire
