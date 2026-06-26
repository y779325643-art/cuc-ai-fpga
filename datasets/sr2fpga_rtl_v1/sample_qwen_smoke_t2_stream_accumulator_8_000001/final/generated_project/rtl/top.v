`timescale 1ns / 1ps
module qwen_smoke_t2_stream_accumulator_8_000001 #(
  parameter DATA_WIDTH = 8
) (
  input  wire         clk,
  input  wire         rst_n,
  input  wire         s_axis_valid,
  output wire         s_axis_ready,
  input  wire [7:0]   s_axis_data,
  output wire         m_axis_valid,
  input  wire         m_axis_ready,
  output wire [7:0]   m_axis_data
);

  // Internal signals for connecting skid buffer to accumulator
  wire [7:0] input_buffer_to_accum_m_axis_data;
  wire       input_buffer_to_accum_m_axis_valid;
  wire       input_buffer_to_accum_m_axis_ready;

  // Instantiate skid buffer
  skid_buffer #(
    .WIDTH(DATA_WIDTH)
  ) input_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(s_axis_valid),
    .s_ready(s_axis_ready),
    .s_data(s_axis_data),
    .m_valid(input_buffer_to_accum_m_axis_valid),
    .m_ready(input_buffer_to_accum_m_axis_ready),
    .m_data(input_buffer_to_accum_m_axis_data)
  );

  // Instantiate accumulator core
  accumulator_core #(
    .WIDTH(DATA_WIDTH)
  ) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(input_buffer_to_accum_m_axis_valid),
    .s_ready(input_buffer_to_accum_m_axis_ready),
    .s_data(input_buffer_to_accum_m_axis_data),
    .m_valid(m_axis_valid),
    .m_ready(m_axis_ready),
    .m_data(m_axis_data)
  );

endmodule
