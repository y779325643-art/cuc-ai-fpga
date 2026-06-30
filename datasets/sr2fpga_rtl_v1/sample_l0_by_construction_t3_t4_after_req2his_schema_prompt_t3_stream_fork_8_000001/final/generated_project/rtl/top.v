module top #(parameter WIDTH = 8, parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out0_valid,
    output wire [WIDTH-1:0] out0_data,
    input wire out0_ready,
    output wire out1_valid,
    output wire [WIDTH-1:0] out1_data,
    input wire out1_ready
);

  wire input_buffer__in_valid;
  wire [DATA_WIDTH-1:0] input_buffer__in_data;
  wire input_buffer__in_ready;
  wire input_buffer__out_valid;
  wire [DATA_WIDTH-1:0] input_buffer__out_data;
  wire input_buffer__out_ready;
  wire fork_core__in_valid;
  wire [DATA_WIDTH-1:0] fork_core__in_data;
  wire fork_core__in_ready;
  wire fork_core__out0_valid;
  wire [DATA_WIDTH-1:0] fork_core__out0_data;
  wire fork_core__out0_ready;
  wire fork_core__out1_valid;
  wire [DATA_WIDTH-1:0] fork_core__out1_data;
  wire fork_core__out1_ready;
  wire out0_stage__in_valid;
  wire [DATA_WIDTH-1:0] out0_stage__in_data;
  wire out0_stage__in_ready;
  wire out0_stage__out_valid;
  wire [DATA_WIDTH-1:0] out0_stage__out_data;
  wire out0_stage__out_ready;
  wire out1_stage__in_valid;
  wire [DATA_WIDTH-1:0] out1_stage__in_data;
  wire out1_stage__in_ready;
  wire out1_stage__out_valid;
  wire [DATA_WIDTH-1:0] out1_stage__out_data;
  wire out1_stage__out_ready;

  assign input_buffer__in_data = in_data;
  assign input_buffer__in_valid = in_valid;
  assign in_ready = input_buffer__in_ready;
  assign fork_core__in_data = input_buffer__out_data;
  assign fork_core__in_valid = input_buffer__out_valid;
  assign input_buffer__out_ready = fork_core__in_ready;
  assign out0_stage__in_data = fork_core__out0_data;
  assign out0_stage__in_valid = fork_core__out0_valid;
  assign fork_core__out0_ready = out0_stage__in_ready;
  assign out0_data = out0_stage__out_data;
  assign out0_valid = out0_stage__out_valid;
  assign out0_stage__out_ready = out0_ready;
  assign out1_stage__in_data = fork_core__out1_data;
  assign out1_stage__in_valid = fork_core__out1_valid;
  assign fork_core__out1_ready = out1_stage__in_ready;
  assign out1_data = out1_stage__out_data;
  assign out1_valid = out1_stage__out_valid;
  assign out1_stage__out_ready = out1_ready;

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

  stream_fork #(.DATA_WIDTH(8)) fork_core (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(fork_core__in_valid),
    .in_data(fork_core__in_data),
    .in_ready(fork_core__in_ready),
    .out0_valid(fork_core__out0_valid),
    .out0_data(fork_core__out0_data),
    .out0_ready(fork_core__out0_ready),
    .out1_valid(fork_core__out1_valid),
    .out1_data(fork_core__out1_data),
    .out1_ready(fork_core__out1_ready)
  );

  stream_stage #(.DATA_WIDTH(8)) out0_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(out0_stage__in_valid),
    .in_data(out0_stage__in_data),
    .in_ready(out0_stage__in_ready),
    .out_valid(out0_stage__out_valid),
    .out_data(out0_stage__out_data),
    .out_ready(out0_stage__out_ready)
  );

  stream_stage #(.DATA_WIDTH(8)) out1_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(out1_stage__in_valid),
    .in_data(out1_stage__in_data),
    .in_ready(out1_stage__in_ready),
    .out_valid(out1_stage__out_valid),
    .out_data(out1_stage__out_data),
    .out_ready(out1_stage__out_ready)
  );

endmodule
