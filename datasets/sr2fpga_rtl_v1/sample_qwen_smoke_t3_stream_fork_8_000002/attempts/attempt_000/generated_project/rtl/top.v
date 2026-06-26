`timescale 1ns/1ps
module top #(
  parameter DATA_WIDTH = 8
) (
  input  wire         clk,
  input  wire         rst_n,
  input  wire         s_valid,
  output wire         s_ready,
  input  wire [DATA_WIDTH-1:0] s_data,
  output wire         m0_valid,
  input  wire         m0_ready,
  output wire [DATA_WIDTH-1:0] m0_data,
  output wire         m1_valid,
  input  wire         m1_ready,
  output wire [DATA_WIDTH-1:0] m1_data
);

  // Internal signals for connecting instances
  wire         input_buffer_s_valid;
  wire         input_buffer_s_ready;
  wire [DATA_WIDTH-1:0] input_buffer_s_data;
  wire         input_buffer_m_valid;
  wire         input_buffer_m_ready;
  wire [DATA_WIDTH-1:0] input_buffer_m_data;

  wire         fork_core_s_valid;
  wire         fork_core_s_ready;
  wire [DATA_WIDTH-1:0] fork_core_s_data;
  wire         fork_core_m0_valid;
  wire         fork_core_m0_ready;
  wire [DATA_WIDTH-1:0] fork_core_m0_data;
  wire         fork_core_m1_valid;
  wire         fork_core_m1_ready;
  wire [DATA_WIDTH-1:0] fork_core_m1_data;

  wire         out0_stage_s_valid;
  wire         out0_stage_s_ready;
  wire [DATA_WIDTH-1:0] out0_stage_s_data;
  wire         out0_stage_m_valid;
  wire         out0_stage_m_ready;
  wire [DATA_WIDTH-1:0] out0_stage_m_data;

  wire         out1_stage_s_valid;
  wire         out1_stage_s_ready;
  wire [DATA_WIDTH-1:0] out1_stage_s_data;
  wire         out1_stage_m_valid;
  wire         out1_stage_m_ready;
  wire [DATA_WIDTH-1:0] out1_stage_m_data;

  // Instance: input_buffer (skid_buffer)
  skid_buffer #(
    .WIDTH(DATA_WIDTH)
  ) input_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(input_buffer_s_valid),
    .s_ready(input_buffer_s_ready),
    .s_data(input_buffer_s_data),
    .m_valid(input_buffer_m_valid),
    .m_ready(input_buffer_m_ready),
    .m_data(input_buffer_m_data)
  );

  // Instance: fork_core (stream_fork)
  stream_fork #(
    .WIDTH(DATA_WIDTH)
  ) fork_core (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(fork_core_s_valid),
    .s_ready(fork_core_s_ready),
    .s_data(fork_core_s_data),
    .m0_valid(fork_core_m0_valid),
    .m0_ready(fork_core_m0_ready),
    .m0_data(fork_core_m0_data),
    .m1_valid(fork_core_m1_valid),
    .m1_ready(fork_core_m1_ready),
    .m1_data(fork_core_m1_data)
  );

  // Instance: out0_stage (stream_stage)
  stream_stage #(
    .WIDTH(DATA_WIDTH)
  ) out0_stage (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(out0_stage_s_valid),
    .s_ready(out0_stage_s_ready),
    .s_data(out0_stage_s_data),
    .m_valid(out0_stage_m_valid),
    .m_ready(out0_stage_m_ready),
    .m_data(out0_stage_m_data)
  );

  // Instance: out1_stage (stream_stage)
  stream_stage #(
    .WIDTH(DATA_WIDTH)
  ) out1_stage (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(out1_stage_s_valid),
    .s_ready(out1_stage_s_ready),
    .s_data(out1_stage_s_data),
    .m_valid(out1_stage_m_valid),
    .m_ready(out1_stage_m_ready),
    .m_data(out1_stage_m_data)
  );

  // Top-level port connections
  assign input_buffer_s_valid = s_valid;
  assign s_ready = input_buffer_s_ready;
  assign input_buffer_s_data = s_data;

  assign fork_core_s_valid = input_buffer_m_valid;
  assign input_buffer_m_ready = fork_core_s_ready;
  assign fork_core_s_data = input_buffer_m_data;

  assign out0_stage_s_valid = fork_core_m0_valid;
  assign fork_core_m0_ready = out0_stage_s_ready;
  assign out0_stage_s_data = fork_core_m0_data;

  assign out1_stage_s_valid = fork_core_m1_valid;
  assign fork_core_m1_ready = out1_stage_s_ready;
  assign out1_stage_s_data = fork_core_m1_data;

  assign m0_valid = out0_stage_m_valid;
  assign out0_stage_m_ready = m0_ready;
  assign m0_data = out0_stage_m_data;

  assign m1_valid = out1_stage_m_valid;
  assign out1_stage_m_ready = m1_ready;
  assign m1_data = out1_stage_m_data;

endmodule
