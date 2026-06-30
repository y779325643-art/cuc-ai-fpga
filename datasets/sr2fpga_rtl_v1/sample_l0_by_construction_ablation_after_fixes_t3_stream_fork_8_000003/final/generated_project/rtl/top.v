module top (
  input wire clk,
  input wire reset_n,
  input wire in_valid,
  input wire [7:0] in_data,
  output wire in_ready,
  output wire out0_valid,
  output wire [7:0] out0_data,
  input wire out0_ready,
  output wire out1_valid,
  output wire [7:0] out1_data,
  input wire out1_ready
);
  wire skid_out_valid, skid_out_ready;
  wire [7:0] skid_out_data;
  wire fork_in_ready;
  wire fork_out0_valid, fork_out0_ready;
  wire [7:0] fork_out0_data;
  wire fork_out1_valid, fork_out1_ready;
  wire [7:0] fork_out1_data;

  skid_buffer u_skid (
    .clk(clk),
    .reset_n(reset_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .in_ready(in_ready),
    .out_valid(skid_out_valid),
    .out_data(skid_out_data),
    .out_ready(skid_out_ready)
  );

  stream_fork u_fork (
    .in_valid(skid_out_valid),
    .in_data(skid_out_data),
    .in_ready(fork_in_ready),
    .out0_valid(fork_out0_valid),
    .out0_data(fork_out0_data),
    .out0_ready(fork_out0_ready),
    .out1_valid(fork_out1_valid),
    .out1_data(fork_out1_data),
    .out1_ready(fork_out1_ready)
  );
  assign skid_out_ready = fork_in_ready;

  stream_stage u_stage0 (
    .clk(clk),
    .reset_n(reset_n),
    .in_valid(fork_out0_valid),
    .in_data(fork_out0_data),
    .in_ready(fork_out0_ready),
    .out_valid(out0_valid),
    .out_data(out0_data),
    .out_ready(out0_ready)
  );

  stream_stage u_stage1 (
    .clk(clk),
    .reset_n(reset_n),
    .in_valid(fork_out1_valid),
    .in_data(fork_out1_data),
    .in_ready(fork_out1_ready),
    .out_valid(out1_valid),
    .out_data(out1_data),
    .out_ready(out1_ready)
  );

endmodule
