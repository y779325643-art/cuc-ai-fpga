module top #(parameter DATA_WIDTH = 8, parameter SUM_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire sample_valid,
    output wire [SUM_WIDTH-1:0] sum
);

  wire input_buffer__in_valid;
  wire [DATA_WIDTH-1:0] input_buffer__in_data;
  wire input_buffer__in_ready;
  wire input_buffer__out_valid;
  wire [DATA_WIDTH-1:0] input_buffer__out_data;
  wire input_buffer__out_ready;
  wire accumulator__sample_valid;
  wire [DATA_WIDTH-1:0] accumulator__sample;
  wire accumulator__sample_ready;
  wire [SUM_WIDTH-1:0] accumulator__sum;

  assign input_buffer__in_data = in_data;
  assign input_buffer__in_valid = in_valid;
  assign in_ready = input_buffer__in_ready;
  assign accumulator__sample = input_buffer__out_data;
  assign accumulator__sample_valid = input_buffer__out_valid;
  assign input_buffer__out_ready = accumulator__sample_ready;
  assign sum = accumulator__sum;
  assign sample_valid = accumulator__sample_valid;

  skid_buffer #(.DATA_WIDTH(8)) input_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(input_buffer__in_valid),
    .in_data(input_buffer__in_data),
    .in_ready(input_buffer__in_ready),
    .out_valid(input_buffer__out_valid),
    .out_data(input_buffer__out_data),
    .out_ready(input_buffer__out_ready)
  );

  accumulator_core #(.DATA_WIDTH(8), .SUM_WIDTH(8)) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(accumulator__sample_valid),
    .sample(accumulator__sample),
    .sample_ready(accumulator__sample_ready),
    .sum(accumulator__sum)
  );

endmodule
