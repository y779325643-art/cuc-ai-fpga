`timescale 1ns/1ps
module stream_fork #(
  parameter WIDTH = 8
) (
  input  wire         clk,
  input  wire         rst_n,
  input  wire         s_valid,
  output wire         s_ready,
  input  wire [WIDTH-1:0] s_data,
  output wire         m0_valid,
  input  wire         m0_ready,
  output wire [WIDTH-1:0] m0_data,
  output wire         m1_valid,
  input  wire         m1_ready,
  output wire [WIDTH-1:0] m1_data
);

  // Fork logic: input is ready only when both outputs are ready
  assign s_ready = m0_ready & m1_ready;
  assign m0_valid = s_valid & s_ready;
  assign m1_valid = s_valid & s_ready;
  assign m0_data = s_data;
  assign m1_data = s_data;

endmodule
