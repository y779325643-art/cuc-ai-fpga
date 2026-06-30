module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    output wire out0_valid,
    input wire out0_ready,
    output wire [7:0] out0_data,
    output wire out1_valid,
    input wire out1_ready,
    output wire [7:0] out1_data
);

  wire fork_valid;
  wire fork_ready;
  wire [7:0] fork_data;
  wire stage0_in_valid;
  wire stage0_in_ready;
  wire [7:0] stage0_in_data;
  wire stage1_in_valid;
  wire stage1_in_ready;
  wire [7:0] stage1_in_data;

  skid_buffer #(
    .WIDTH(8)
  ) u_skid_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out_valid(fork_valid),
    .out_ready(fork_ready),
    .out_data(fork_data)
  );

  stream_fork #(
    .WIDTH(8)
  ) u_stream_fork (
    .in_valid(fork_valid),
    .in_ready(fork_ready),
    .in_data(fork_data),
    .out0_valid(stage0_in_valid),
    .out0_ready(stage0_in_ready),
    .out0_data(stage0_in_data),
    .out1_valid(stage1_in_valid),
    .out1_ready(stage1_in_ready),
    .out1_data(stage1_in_data)
  );

  stream_stage #(
    .WIDTH(8)
  ) u_stage0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(stage0_in_valid),
    .in_ready(stage0_in_ready),
    .in_data(stage0_in_data),
    .out_valid(out0_valid),
    .out_ready(out0_ready),
    .out_data(out0_data)
  );

  stream_stage #(
    .WIDTH(8)
  ) u_stage1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(stage1_in_valid),
    .in_ready(stage1_in_ready),
    .in_data(stage1_in_data),
    .out_valid(out1_valid),
    .out_ready(out1_ready),
    .out_data(out1_data)
  );

endmodule
