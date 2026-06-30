module stream_join (
  input  wire        clk,
  input  wire        rst_n,
  input  wire        in0_valid,
  input  wire [7:0]  in0_data,
  output wire        in0_ready,
  input  wire        in1_valid,
  input  wire [7:0]  in1_data,
  output wire        in1_ready,
  output wire        out_valid,
  output wire [7:0]  out_data,
  input  wire        out_ready
);

  // Join: output valid only when both inputs are valid
  assign out_valid = in0_valid & in1_valid;

  // Sum the two data streams
  assign out_data = in0_data + in1_data;

  // Ready to accept both inputs when downstream ready and both inputs valid
  wire both_valid = in0_valid & in1_valid;
  assign in0_ready = out_ready & both_valid;
  assign in1_ready = out_ready & both_valid;

endmodule
