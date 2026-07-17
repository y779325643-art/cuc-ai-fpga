module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    input wire accum_ready,
    output wire sample_valid,
    output wire [11:0] sum
);

  wire [7:0] sample_data;

  skid_buffer #(
    .WIDTH(8)
  ) u_skid_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out_valid(sample_valid),
    .out_ready(accum_ready),
    .out_data(sample_data)
  );

  accumulator_core #(
    .WIDTH(8),
    .SUM_WIDTH(12)
  ) u_accumulator_core (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(sample_valid),
    .sample_ready(accum_ready),
    .sample(sample_data),
    .sum(sum)
  );

endmodule
