module top #(parameter DATA_WIDTH = 8, parameter WIDTH_A = 8, parameter WIDTH_B = 8, parameter OUTPUT_WIDTH = 16) (
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
  wire [DATA_WIDTH-1:0] in0_buffer__in_data;
  wire in0_buffer__in_ready;
  wire in0_buffer__out_valid;
  wire [DATA_WIDTH-1:0] in0_buffer__out_data;
  wire in0_buffer__out_ready;
  wire in1_buffer__in_valid;
  wire [DATA_WIDTH-1:0] in1_buffer__in_data;
  wire in1_buffer__in_ready;
  wire in1_buffer__out_valid;
  wire [DATA_WIDTH-1:0] in1_buffer__out_data;
  wire in1_buffer__out_ready;
  wire join_core__a_valid;
  wire [WIDTH_A-1:0] join_core__a_data;
  wire join_core__a_ready;
  wire join_core__b_valid;
  wire [WIDTH_B-1:0] join_core__b_data;
  wire join_core__b_ready;
  wire join_core__out_valid;
  wire [OUTPUT_WIDTH-1:0] join_core__out_data;
  wire join_core__out_ready;
  wire accumulator__sample_valid;
  wire [DATA_WIDTH-1:0] accumulator__sample_data;
  wire accumulator__sample_ready;
  wire accumulator__out_valid;
  wire [DATA_WIDTH-1:0] accumulator__out_data;
  wire accumulator__out_ready;
  wire out_stage__in_valid;
  wire [DATA_WIDTH-1:0] out_stage__in_data;
  wire out_stage__in_ready;
  wire out_stage__out_valid;
  wire [DATA_WIDTH-1:0] out_stage__out_data;
  wire out_stage__out_ready;

  assign in0_buffer__in_valid = in0_valid;
  assign in0_ready = in0_buffer__in_ready;
  assign in0_buffer__in_data = in0_data;
  assign in1_buffer__in_valid = in1_valid;
  assign in1_ready = in1_buffer__in_ready;
  assign in1_buffer__in_data = in1_data;
  assign join_core__a_data = in0_buffer__out_data;
  assign join_core__a_valid = in0_buffer__out_valid;
  assign in0_buffer__out_ready = join_core__a_ready;
  assign join_core__b_data = in1_buffer__out_data;
  assign join_core__b_valid = in1_buffer__out_valid;
  assign in1_buffer__out_ready = join_core__b_ready;
  assign accumulator__sample_data = join_core__out_data;
  assign accumulator__sample_valid = join_core__out_valid;
  assign join_core__out_ready = accumulator__sample_ready;
  assign out_stage__in_data = accumulator__out_data;
  assign out_stage__in_valid = accumulator__out_valid;
  assign accumulator__out_ready = out_stage__in_ready;
  assign out_data = out_stage__out_data;
  assign out_valid = out_stage__out_valid;
  assign out_stage__out_ready = out_ready;
  assign out_stage__in_ready = out_ready;

  skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_buffer__in_valid),
    .in_data(in0_buffer__in_data),
    .in_ready(in0_buffer__in_ready),
    .out_valid(in0_buffer__out_valid),
    .out_data(in0_buffer__out_data),
    .out_ready(in0_buffer__out_ready)
  );

  skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_buffer__in_valid),
    .in_data(in1_buffer__in_data),
    .in_ready(in1_buffer__in_ready),
    .out_valid(in1_buffer__out_valid),
    .out_data(in1_buffer__out_data),
    .out_ready(in1_buffer__out_ready)
  );

  stream_join #(.WIDTH_A(WIDTH_A), .WIDTH_B(WIDTH_B), .OUTPUT_WIDTH(OUTPUT_WIDTH)) join_core (
    .clk(clk),
    .rst_n(rst_n),
    .a_valid(join_core__a_valid),
    .a_data(join_core__a_data),
    .a_ready(join_core__a_ready),
    .b_valid(join_core__b_valid),
    .b_data(join_core__b_data),
    .b_ready(join_core__b_ready),
    .out_valid(join_core__out_valid),
    .out_data(join_core__out_data),
    .out_ready(join_core__out_ready)
  );

  accumulator_core #(.DATA_WIDTH(DATA_WIDTH)) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(accumulator__sample_valid),
    .sample_data(accumulator__sample_data),
    .sample_ready(accumulator__sample_ready),
    .out_valid(accumulator__out_valid),
    .out_data(accumulator__out_data),
    .out_ready(accumulator__out_ready)
  );

  stream_stage #(.DATA_WIDTH(DATA_WIDTH)) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(out_stage__in_valid),
    .in_data(out_stage__in_data),
    .in_ready(out_stage__in_ready),
    .out_valid(out_stage__out_valid),
    .out_data(out_stage__out_data),
    .out_ready(out_stage__out_ready)
  );

endmodule
