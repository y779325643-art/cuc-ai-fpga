`timescale 1ns / 1ps
module top #(
  parameter DATA_WIDTH = 8
) (
  input  wire         clk,
  input  wire         rst_n,
  input  wire [7:0]   in0_data,
  input  wire         in0_valid,
  output wire         in0_ready,
  input  wire [7:0]   in1_data,
  input  wire         in1_valid,
  output wire         in1_ready,
  output wire [7:0]   out_data,
  output wire         out_valid,
  input  wire         out_ready
);

  // Internal signals for connecting instances
  wire [7:0] in0_buf_out_data;
  wire       in0_buf_out_valid;
  wire       in0_buf_in_ready;
  wire       in0_buf_out_ready;
  
  wire [7:0] in1_buf_out_data;
  wire       in1_buf_out_valid;
  wire       in1_buf_in_ready;
  wire       in1_buf_out_ready;
  
  wire [7:0] join_out_data;
  wire       join_out_valid;
  wire       join_out_ready;
  
  wire [7:0] accum_out_data;
  wire       accum_out_valid;
  wire       accum_out_ready;
  
  wire [7:0] stage_out_data;
  wire       stage_out_valid;
  wire       stage_out_ready;

  // Instance: in0_buffer
  skid_buffer #(
    .DATA_WIDTH(DATA_WIDTH)
  ) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in0_data),
    .in_valid(in0_valid),
    .in_ready(in0_buf_in_ready),
    .out_data(in0_buf_out_data),
    .out_valid(in0_buf_out_valid),
    .out_ready(in0_buf_out_ready)
  );

  // Instance: in1_buffer
  skid_buffer #(
    .DATA_WIDTH(DATA_WIDTH)
  ) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in1_data),
    .in_valid(in1_valid),
    .in_ready(in1_buf_in_ready),
    .out_data(in1_buf_out_data),
    .out_valid(in1_buf_out_valid),
    .out_ready(in1_buf_out_ready)
  );

  // Instance: join_core
  stream_join #(
    .DATA_WIDTH(DATA_WIDTH)
  ) join_core (
    .clk(clk),
    .rst_n(rst_n),
    .in0_data(in0_buf_out_data),
    .in0_valid(in0_buf_out_valid),
    .in0_ready(in0_buf_out_ready),
    .in1_data(in1_buf_out_data),
    .in1_valid(in1_buf_out_valid),
    .in1_ready(in1_buf_out_ready),
    .out_data(join_out_data),
    .out_valid(join_out_valid),
    .out_ready(join_out_ready)
  );

  // Instance: accumulator
  accumulator_core #(
    .DATA_WIDTH(DATA_WIDTH)
  ) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(join_out_data),
    .in_valid(join_out_valid),
    .in_ready(accum_out_ready),
    .out_data(accum_out_data),
    .out_valid(accum_out_valid),
    .out_ready(accum_out_ready)
  );

  // Instance: out_stage
  stream_stage #(
    .DATA_WIDTH(DATA_WIDTH)
  ) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(accum_out_data),
    .in_valid(accum_out_valid),
    .in_ready(stage_out_ready),
    .out_data(stage_out_data),
    .out_valid(stage_out_valid),
    .out_ready(stage_out_ready)
  );

  // Connect top-level ports
  assign in0_ready = in0_buf_in_ready;
  assign in1_ready = in1_buf_in_ready;
  assign out_data = stage_out_data;
  assign out_valid = stage_out_valid;
  assign accum_out_ready = stage_out_ready;
  assign join_out_ready = accum_out_ready;

endmodule
