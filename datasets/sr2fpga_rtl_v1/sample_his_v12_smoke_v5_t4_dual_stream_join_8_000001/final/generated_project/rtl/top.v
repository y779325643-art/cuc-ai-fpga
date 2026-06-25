module top (
  input clk, reset_n,
  input in0_valid, input [7:0] in0_data, output in0_ready,
  input in1_valid, input [7:0] in1_data, output in1_ready,
  output out_valid, output [7:0] out_data, input out_ready
);

wire [7:0] buf0_data, buf1_data;
wire buf0_valid, buf1_valid;
wire buf0_ready_in, buf1_ready_in;

skid_buffer #(.W(8)) in0_buffer (
  .clk(clk), .reset_n(reset_n),
  .valid_in(in0_valid), .data_in(in0_data), .ready_out(in0_ready),
  .valid_out(buf0_valid), .data_out(buf0_data),
  .ready_in(buf0_ready_in)
);

skid_buffer #(.W(8)) in1_buffer (
  .clk(clk), .reset_n(reset_n),
  .valid_in(in1_valid), .data_in(in1_data), .ready_out(in1_ready),
  .valid_out(buf1_valid), .data_out(buf1_data),
  .ready_in(buf1_ready_in)
);

wire [7:0] join_data;
wire join_valid;
wire join_ready_in;
wire join_ready0, join_ready1;

stream_join #(.W(8)) join_core (
  .clk(clk), .reset_n(reset_n),
  .valid0(buf0_valid), .data0(buf0_data), .ready0(join_ready0),
  .valid1(buf1_valid), .data1(buf1_data), .ready1(join_ready1),
  .valid_out(join_valid), .data_out(join_data),
  .ready_in(join_ready_in)
);

assign buf0_ready_in = join_ready0;
assign buf1_ready_in = join_ready1;

wire [7:0] acc_data;
wire acc_valid;
wire acc_ready_in;

accumulator_core #(.W(8)) accumulator (
  .clk(clk), .reset_n(reset_n),
  .valid_in(join_valid), .data_in(join_data), .ready_out(join_ready_in),
  .valid_out(acc_valid), .data_out(acc_data),
  .ready_in(acc_ready_in)
);

wire [7:0] out_data_in;
wire out_valid_in;
wire out_ready_out;

stream_stage #(.W(8)) out_stage (
  .clk(clk), .reset_n(reset_n),
  .valid_in(acc_valid), .data_in(acc_data), .ready_out(acc_ready_in),
  .valid_out(out_valid_in), .data_out(out_data_in),
  .ready_in(out_ready)
);

assign out_valid = out_valid_in;
assign out_data = out_data_in;

endmodule
