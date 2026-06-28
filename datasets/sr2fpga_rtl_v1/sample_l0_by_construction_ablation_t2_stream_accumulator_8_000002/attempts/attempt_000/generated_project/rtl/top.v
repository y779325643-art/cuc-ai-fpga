module top (
  input clk,
  input rst_n,
  input [7:0] in_data,
  input in_valid,
  output in_ready,
  output [7:0] sum
);

  wire [7:0] skid_out_data;
  wire skid_out_valid;
  wire skid_out_ready;

  skid_buffer u_skid (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in_data),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .out_data(skid_out_data),
    .out_valid(skid_out_valid),
    .out_ready(skid_out_ready)
  );

  accumulator_core u_acc (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(skid_out_valid),
    .sample(skid_out_data),
    .sample_ready(skid_out_ready),
    .sum(sum)
  );

endmodule
