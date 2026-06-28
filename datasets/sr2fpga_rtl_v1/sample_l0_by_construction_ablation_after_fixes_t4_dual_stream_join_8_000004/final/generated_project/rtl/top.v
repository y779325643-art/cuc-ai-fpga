`timescale 1ns / 1ps
module top (
  input clk,
  input rst_n,
  input in0_valid,
  input [7:0] in0_data,
  output in0_ready,
  input in1_valid,
  input [7:0] in1_data,
  output in1_ready,
  output out_valid,
  output [15:0] out_data,
  input out_ready
);

  // Interconnect wires
  wire sb0_in_valid, sb0_in_ready;
  wire [7:0] sb0_in_data;
  wire sb0_out_valid, sb0_out_ready;
  wire [7:0] sb0_out_data;

  wire sb1_in_valid, sb1_in_ready;
  wire [7:0] sb1_in_data;
  wire sb1_out_valid, sb1_out_ready;
  wire [7:0] sb1_out_data;

  wire sj_out_valid, sj_out_ready;
  wire [15:0] sj_out_data;

  wire acc_out_valid, acc_out_ready;
  wire [15:0] acc_out_data;

  wire ss_out_valid, ss_out_ready;
  wire [15:0] ss_out_data;

  // Instantiate skid buffer for input 0
  skid_buffer #(.WIDTH(8)) u_skid0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_valid),
    .in_data(in0_data),
    .in_ready(in0_ready),
    .out_valid(sb0_out_valid),
    .out_data(sb0_out_data),
    .out_ready(sb0_out_ready)
  );

  // Instantiate skid buffer for input 1
  skid_buffer #(.WIDTH(8)) u_skid1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_valid),
    .in_data(in1_data),
    .in_ready(in1_ready),
    .out_valid(sb1_out_valid),
    .out_data(sb1_out_data),
    .out_ready(sb1_out_ready)
  );

  // Instantiate stream join
  stream_join #(.WIDTH(8)) u_join (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(sb0_out_valid),
    .in0_data(sb0_out_data),
    .in0_ready(sb0_out_ready),
    .in1_valid(sb1_out_valid),
    .in1_data(sb1_out_data),
    .in1_ready(sb1_out_ready),
    .out_valid(sj_out_valid),
    .out_data(sj_out_data),
    .out_ready(sj_out_ready)
  );

  // Instantiate accumulator core
  accumulator_core #(.NUM_SAMPLES(4), .WIDTH(16)) u_acc (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(sj_out_valid),
    .sample(sj_out_data),
    .sample_ready(sj_out_ready),
    .sum_valid(acc_out_valid),
    .sum(acc_out_data),
    .sum_ready(acc_out_ready)
  );

  // Instantiate stream stage
  stream_stage #(.WIDTH(16)) u_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(acc_out_valid),
    .in_data(acc_out_data),
    .in_ready(acc_out_ready),
    .out_valid(ss_out_valid),
    .out_data(ss_out_data),
    .out_ready(ss_out_ready)
  );

  assign out_valid = ss_out_valid;
  assign out_data = ss_out_data;
  assign ss_out_ready = out_ready;

endmodule
