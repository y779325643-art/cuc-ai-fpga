module top (
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
  wire sb0_out_valid, sb1_out_valid;
  wire [7:0] sb0_out_data, sb1_out_data;
  wire sb0_out_ready, sb1_out_ready;
  wire join_out_valid;
  wire [7:0] join_out_data;
  wire join_out_ready;
  wire acc_sample_valid;
  wire [7:0] acc_sample;
  wire acc_sample_ready;
  wire acc_out_valid;
  wire [7:0] acc_sum;
  wire stage_in_ready;
  skid_buffer sb0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_valid),
    .in_data(in0_data),
    .in_ready(in0_ready),
    .out_valid(sb0_out_valid),
    .out_data(sb0_out_data),
    .out_ready(sb0_out_ready)
  );
  skid_buffer sb1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_valid),
    .in_data(in1_data),
    .in_ready(in1_ready),
    .out_valid(sb1_out_valid),
    .out_data(sb1_out_data),
    .out_ready(sb1_out_ready)
  );
  stream_join join (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(sb0_out_valid),
    .in0_data(sb0_out_data),
    .in0_ready(sb0_out_ready),
    .in1_valid(sb1_out_valid),
    .in1_data(sb1_out_data),
    .in1_ready(sb1_out_ready),
    .out_valid(join_out_valid),
    .out_data(join_out_data),
    .out_ready(join_out_ready)
  );
  accumulator_core acc (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(join_out_valid),
    .sample(join_out_data),
    .sample_ready(join_out_ready),
    .sum_valid(acc_out_valid),
    .sum(acc_sum),
    .sum_ready(stage_in_ready)
  );
  stream_stage stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(acc_out_valid),
    .in_data(acc_sum),
    .in_ready(stage_in_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(out_ready)
  );
endmodule
