module top #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [7:0] in0_data,
    output wire in0_ready,
    input wire in1_valid,
    input wire [7:0] in1_data,
    output wire in1_ready,
    output wire out_valid,
    output wire [7:0] out_data,
    input wire out_ready
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
  wire accumulator__sample_valid;
  wire accumulator__sample_ready;
  wire [DATA_WIDTH-1:0] accumulator__sample;
  wire accumulator__sum_valid;
  wire accumulator__sum_ready;
  wire [DATA_WIDTH-1:0] accumulator__sum;
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
  assign accumulator__sample_valid = join_core__out_valid;
  assign join_core__out_ready = accumulator__sample_ready;
  assign out_stage__in_data = accumulator__sum;
  assign out_stage__in_valid = accumulator__sum_valid;
  assign accumulator__sum_ready = out_stage__in_ready;
  assign out_data = out_stage__out_data;
  assign out_valid = out_stage__out_valid;
  assign out_stage__out_ready = out_ready;

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
    .sample_valid(accumulator__sample_valid),
    .sample_ready(accumulator__sample_ready),
    .sample(accumulator__sample),
    .sum_valid(accumulator__sum_valid),
    .sum_ready(accumulator__sum_ready),
    .sum(accumulator__sum)
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
