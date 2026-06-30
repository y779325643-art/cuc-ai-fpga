module stream_fork (
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
  assign in_ready = out0_ready & out1_ready;
  assign out0_valid = in_valid;
  assign out0_data = in_data;
  assign out1_valid = in_valid;
  assign out1_data = in_data;
endmodule
