module top (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    output wire in0_ready,
    input wire [7:0] in0_data,
    input wire in1_valid,
    output wire in1_ready,
    input wire [7:0] in1_data,
    output wire out_valid,
    input wire out_ready,
    output wire [11:0] out_data
);

  wire s0_valid;
  wire s0_ready;
  wire [7:0] s0_data;
  wire s1_valid;
  wire s1_ready;
  wire [7:0] s1_data;
  wire joined_valid;
  wire joined_ready;
  wire [7:0] joined_data;
  wire accum_valid;
  wire accum_ready;
  wire [11:0] accum_sum;

  skid_buffer #(
    .WIDTH(8)
  ) u_skid0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in0_valid),
    .in_ready(in0_ready),
    .in_data(in0_data),
    .out_valid(s0_valid),
    .out_ready(s0_ready),
    .out_data(s0_data)
  );

  skid_buffer #(
    .WIDTH(8)
  ) u_skid1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in1_valid),
    .in_ready(in1_ready),
    .in_data(in1_data),
    .out_valid(s1_valid),
    .out_ready(s1_ready),
    .out_data(s1_data)
  );

  stream_join #(
    .WIDTH(8)
  ) u_stream_join (
    .in0_valid(s0_valid),
    .in0_ready(s0_ready),
    .in0_data(s0_data),
    .in1_valid(s1_valid),
    .in1_ready(s1_ready),
    .in1_data(s1_data),
    .out_valid(joined_valid),
    .out_ready(joined_ready),
    .out_data(joined_data)
  );

  accumulator_core #(
    .WIDTH(8)
  ) u_accumulator_core (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(joined_valid),
    .sample_ready(joined_ready),
    .sample(joined_data),
    .sum(accum_sum)
  );

  assign accum_valid = joined_valid && joined_ready;

  stream_stage #(
    .WIDTH(12)
  ) u_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(accum_valid),
    .in_ready(accum_ready),
    .in_data(accum_sum),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
  );

endmodule
