`timescale 1ns / 1ps

module top #(
  parameter DATA_WIDTH = 8
) (
  input  wire                clk,
  input  wire                rst_n,
  input  wire                in0_valid,
  output wire                in0_ready,
  input  wire [DATA_WIDTH-1:0] in0_data,
  input  wire                in1_valid,
  output wire                in1_ready,
  input  wire [DATA_WIDTH-1:0] in1_data,
  output wire                out_valid,
  input  wire                out_ready,
  output wire [DATA_WIDTH-1:0] out_data
);

  // Internal wires
  wire [DATA_WIDTH-1:0] buffer0_out_data;
  wire buffer0_out_valid;
  wire [DATA_WIDTH-1:0] buffer1_out_data;
  wire buffer1_out_valid;
  wire [DATA_WIDTH-1:0] join_out_data;
  wire join_out_valid;
  wire join_in0_ready;
  wire join_in1_ready;
  wire [DATA_WIDTH-1:0] acc_out_data;
  wire acc_out_valid;
  wire acc_in_ready;
  wire stage_in_ready;

  // Instantiate skid_buffer for input 0
  skid_buffer #(
    .DATA_WIDTH(DATA_WIDTH)
  ) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_valid),
    .in_ready(in0_ready),
    .in_data(in0_data),
    .out_valid(buffer0_out_valid),
    .out_ready(join_in0_ready),
    .out_data(buffer0_out_data)
  );

  // Instantiate skid_buffer for input 1
  skid_buffer #(
    .DATA_WIDTH(DATA_WIDTH)
  ) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_valid),
    .in_ready(in1_ready),
    .in_data(in1_data),
    .out_valid(buffer1_out_valid),
    .out_ready(join_in1_ready),
    .out_data(buffer1_out_data)
  );

  // Instantiate stream_join
  stream_join #(
    .DATA_WIDTH(DATA_WIDTH)
  ) join_core (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(buffer0_out_valid),
    .in0_ready(join_in0_ready),
    .in0_data(buffer0_out_data),
    .in1_valid(buffer1_out_valid),
    .in1_ready(join_in1_ready),
    .in1_data(buffer1_out_data),
    .out_valid(join_out_valid),
    .out_ready(acc_in_ready),
    .out_data(join_out_data)
  );

  // Instantiate accumulator_core
  accumulator_core #(
    .DATA_WIDTH(DATA_WIDTH)
  ) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(join_out_valid),
    .in_ready(acc_in_ready),
    .in_data(join_out_data),
    .out_valid(acc_out_valid),
    .out_ready(stage_in_ready),
    .out_data(acc_out_data)
  );

  // Instantiate stream_stage
  stream_stage #(
    .DATA_WIDTH(DATA_WIDTH)
  ) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(acc_out_valid),
    .in_ready(stage_in_ready),
    .in_data(acc_out_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
  );

endmodule
