module top #(parameter DATA_WIDTH=8) (
  input clk, rst_n,
  input [DATA_WIDTH-1:0] in0_data,
  input in0_valid,
  output in0_ready,
  input [DATA_WIDTH-1:0] in1_data,
  input in1_valid,
  output in1_ready,
  output [DATA_WIDTH-1:0] out_data,
  output out_valid,
  input out_ready
);

  wire [DATA_WIDTH-1:0] buf0_out, buf1_out;
  wire buf0_valid, buf1_valid;
  wire buf0_ready, buf1_ready;

  skid_buffer #(.W(DATA_WIDTH)) in0_buffer (
    .clk(clk), .rst_n(rst_n),
    .data_in(in0_data), .valid_in(in0_valid), .ready_out(in0_ready),
    .data_out(buf0_out), .valid_out(buf0_valid), .ready_in(buf0_ready)
  );

  skid_buffer #(.W(DATA_WIDTH)) in1_buffer (
    .clk(clk), .rst_n(rst_n),
    .data_in(in1_data), .valid_in(in1_valid), .ready_out(in1_ready),
    .data_out(buf1_out), .valid_out(buf1_valid), .ready_in(buf1_ready)
  );

  wire [DATA_WIDTH-1:0] join_out;
  wire join_valid;
  wire join_ready;

  stream_join #(.W(DATA_WIDTH)) join_core (
    .clk(clk), .rst_n(rst_n),
    .input0_data(buf0_out), .input0_valid(buf0_valid), .input0_ready(buf0_ready),
    .input1_data(buf1_out), .input1_valid(buf1_valid), .input1_ready(buf1_ready),
    .output_data(join_out), .output_valid(join_valid), .output_ready(join_ready)
  );

  wire [DATA_WIDTH-1:0] acc_out;
  wire acc_valid;
  wire acc_ready;

  accumulator_core #(.W(DATA_WIDTH)) accumulator (
    .clk(clk), .rst_n(rst_n),
    .data_in(join_out), .valid_in(join_valid), .ready_out(join_ready),
    .data_out(acc_out), .valid_out(acc_valid), .ready_in(acc_ready)
  );

  wire [DATA_WIDTH-1:0] stage_out;
  wire stage_valid;

  stream_stage #(.W(DATA_WIDTH)) out_stage (
    .clk(clk), .rst_n(rst_n),
    .data_in(acc_out), .valid_in(acc_valid), .ready_out(acc_ready),
    .data_out(stage_out), .valid_out(stage_valid), .ready_in(out_ready)
  );

  assign out_data = stage_out;
  assign out_valid = stage_valid;

endmodule
