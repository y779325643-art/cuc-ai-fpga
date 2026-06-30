module top #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [7:0] in0_data,
    input wire in1_valid,
    input wire [7:0] in1_data,
    input wire out_ready,
    output wire in0_ready,
    output wire in1_ready,
    output wire out_valid,
    output wire [7:0] out_data
);

  wire in0_buffer__in_valid;
  wire in0_buffer__in_ready;
  wire [DATA_WIDTH-1:0] in0_buffer__in_data;
  wire in0_buffer__out_valid;
  wire in0_buffer__out_ready;
  wire [DATA_WIDTH-1:0] in0_buffer__out_data;
  wire in1_buffer__in_valid;
  wire in1_buffer__in_ready;
  wire [DATA_WIDTH-1:0] in1_buffer__in_data;
  wire in1_buffer__out_valid;
  wire in1_buffer__out_ready;
  wire [DATA_WIDTH-1:0] in1_buffer__out_data;
  wire join_core__in0_valid;
  wire join_core__in0_ready;
  wire [DATA_WIDTH-1:0] join_core__in0_data;
  wire join_core__in1_valid;
  wire join_core__in1_ready;
  wire [DATA_WIDTH-1:0] join_core__in1_data;
  wire join_core__out_valid;
  wire join_core__out_ready;
  wire [DATA_WIDTH-1:0] join_core__out_data;
  wire accumulator__sample_valid_in;
  wire accumulator__sample_ready_out;
  wire [DATA_WIDTH-1:0] accumulator__sample;
  wire [DATA_WIDTH-1:0] accumulator__sum;
  wire accumulator__sample_valid_out;
  wire out_stage__in_valid;
  wire out_stage__in_ready;
  wire [DATA_WIDTH-1:0] out_stage__in_data;
  wire out_stage__out_valid;
  wire out_stage__out_ready;
  wire [DATA_WIDTH-1:0] out_stage__out_data;

  assign in0_buffer__in_data = in0_data;
  assign in0_buffer__in_valid = in0_valid;
  assign in0_ready = in0_buffer__in_ready;
  assign join_core__in0_data = in0_buffer__out_data;
  assign join_core__in0_valid = in0_buffer__out_valid;
  assign in0_buffer__out_ready = join_core__in0_ready;
  assign in1_buffer__in_data = in1_data;
  assign in1_buffer__in_valid = in1_valid;
  assign in1_ready = in1_buffer__in_ready;
  assign join_core__in1_data = in1_buffer__out_data;
  assign join_core__in1_valid = in1_buffer__out_valid;
  assign in1_buffer__out_ready = join_core__in1_ready;
  assign accumulator__sample = join_core__out_data;
  assign join_core__out_ready = out_stage__in_ready;
  assign out_stage__in_data = accumulator__sum;
  assign out_stage__in_valid = accumulator__sample_valid_out;
  assign out_data = out_stage__out_data;
  assign out_valid = out_stage__out_valid;
  assign out_stage__out_ready = out_ready;
  assign accumulator__sample_valid_in = join_core__out_valid;
  assign accumulator__sample_ready_out = out_stage__in_ready;
  wire _unused_data_flow_signals = &{1'b0, join_core__out_valid, out_stage__in_ready};

  skid_buffer #(.DATA_WIDTH(8)) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_buffer__in_valid),
    .in_ready(in0_buffer__in_ready),
    .in_data(in0_buffer__in_data),
    .out_valid(in0_buffer__out_valid),
    .out_ready(in0_buffer__out_ready),
    .out_data(in0_buffer__out_data)
  );

  skid_buffer #(.DATA_WIDTH(8)) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_buffer__in_valid),
    .in_ready(in1_buffer__in_ready),
    .in_data(in1_buffer__in_data),
    .out_valid(in1_buffer__out_valid),
    .out_ready(in1_buffer__out_ready),
    .out_data(in1_buffer__out_data)
  );

  stream_join #(.DATA_WIDTH(8)) join_core (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(join_core__in0_valid),
    .in0_ready(join_core__in0_ready),
    .in0_data(join_core__in0_data),
    .in1_valid(join_core__in1_valid),
    .in1_ready(join_core__in1_ready),
    .in1_data(join_core__in1_data),
    .out_valid(join_core__out_valid),
    .out_ready(join_core__out_ready),
    .out_data(join_core__out_data)
  );

  accumulator_core #(.DATA_WIDTH(8)) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid_in(accumulator__sample_valid_in),
    .sample_ready_out(accumulator__sample_ready_out),
    .sample(accumulator__sample),
    .sum(accumulator__sum),
    .sample_valid_out(accumulator__sample_valid_out)
  );

  stream_stage #(.DATA_WIDTH(8)) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(out_stage__in_valid),
    .in_ready(out_stage__in_ready),
    .in_data(out_stage__in_data),
    .out_valid(out_stage__out_valid),
    .out_ready(out_stage__out_ready),
    .out_data(out_stage__out_data)
  );

endmodule
