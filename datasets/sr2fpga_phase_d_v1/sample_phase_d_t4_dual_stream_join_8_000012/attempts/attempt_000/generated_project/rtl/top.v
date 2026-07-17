module top #(parameter DATA_WIDTH = 8, parameter ACCUM_WIDTH = 16) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [DATA_WIDTH-1:0] in0_data,
    input wire in1_valid,
    input wire [DATA_WIDTH-1:0] in1_data,
    input wire out_ready,
    output wire in0_ready,
    output wire in1_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data
);

  wire in0_buffer__in_valid;
  wire [DATA_WIDTH-1:0] in0_buffer__in_data;
  wire in0_buffer__out_ready;
  wire in0_buffer__in_ready;
  wire in0_buffer__out_valid;
  wire [DATA_WIDTH-1:0] in0_buffer__out_data;
  wire in1_buffer__in_valid;
  wire [DATA_WIDTH-1:0] in1_buffer__in_data;
  wire in1_buffer__out_ready;
  wire in1_buffer__in_ready;
  wire in1_buffer__out_valid;
  wire [DATA_WIDTH-1:0] in1_buffer__out_data;
  wire join_core__in0_valid;
  wire [DATA_WIDTH-1:0] join_core__in0_data;
  wire join_core__in1_valid;
  wire [DATA_WIDTH-1:0] join_core__in1_data;
  wire join_core__out_ready;
  wire join_core__in0_ready;
  wire join_core__in1_ready;
  wire join_core__out_valid;
  wire [2*DATA_WIDTH-1:0] join_core__out_data;
  wire accumulator__sample_valid;
  wire [2*DATA_WIDTH-1:0] accumulator__sample_data;
  wire accumulator__sample_ready;
  wire accumulator__out_valid;
  wire [DATA_WIDTH-1:0] accumulator__out_data;
  wire accumulator__in_ready;
  wire out_stage__in_valid;
  wire [DATA_WIDTH-1:0] out_stage__in_data;
  wire out_stage__out_ready;
  wire out_stage__in_ready;
  wire out_stage__out_valid;
  wire [DATA_WIDTH-1:0] out_stage__out_data;

  assign in0_buffer__in_valid = in0_data;
  assign in0_ready = in0_buffer__in_ready;
  assign join_core__in0_valid = in0_buffer__out_data;
  assign in0_buffer__out_ready = join_core__in0_ready;
  assign in1_buffer__in_valid = in1_data;
  assign in1_ready = in1_buffer__in_ready;
  assign join_core__in1_valid = in1_buffer__out_data;
  assign in1_buffer__out_ready = join_core__in1_ready;
  assign accumulator__sample_valid = join_core__out_data;
  assign join_core__out_ready = accumulator__sample_ready;
  assign out_stage__in_valid = accumulator__out_data;
  assign out_valid = out_stage__out_data;
  assign out_stage__out_ready = out_ready;
  assign accumulator__sample_ready = out_stage__in_ready;
  wire _unused_data_flow_signals = &{1'b0, accumulator__out_valid, in0_buffer__out_valid, in0_valid, in1_buffer__out_valid, in1_valid, join_core__out_valid, out_stage__in_ready, out_stage__out_valid};

  skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_buffer__in_valid),
    .in_data(in0_buffer__in_data),
    .out_ready(in0_buffer__out_ready),
    .in_ready(in0_buffer__in_ready),
    .out_valid(in0_buffer__out_valid),
    .out_data(in0_buffer__out_data)
  );

  skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_buffer__in_valid),
    .in_data(in1_buffer__in_data),
    .out_ready(in1_buffer__out_ready),
    .in_ready(in1_buffer__in_ready),
    .out_valid(in1_buffer__out_valid),
    .out_data(in1_buffer__out_data)
  );

  stream_join #(.DATA_WIDTH(DATA_WIDTH)) join_core (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(join_core__in0_valid),
    .in0_data(join_core__in0_data),
    .in1_valid(join_core__in1_valid),
    .in1_data(join_core__in1_data),
    .out_ready(join_core__out_ready),
    .in0_ready(join_core__in0_ready),
    .in1_ready(join_core__in1_ready),
    .out_valid(join_core__out_valid),
    .out_data(join_core__out_data)
  );

  accumulator_core #(.DATA_WIDTH(DATA_WIDTH), .ACCUM_WIDTH(ACCUM_WIDTH)) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(accumulator__sample_valid),
    .sample_data(accumulator__sample_data),
    .sample_ready(accumulator__sample_ready),
    .out_valid(accumulator__out_valid),
    .out_data(accumulator__out_data),
    .in_ready(accumulator__in_ready)
  );

  stream_stage #(.DATA_WIDTH(DATA_WIDTH)) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(out_stage__in_valid),
    .in_data(out_stage__in_data),
    .out_ready(out_stage__out_ready),
    .in_ready(out_stage__in_ready),
    .out_valid(out_stage__out_valid),
    .out_data(out_stage__out_data)
  );

endmodule
