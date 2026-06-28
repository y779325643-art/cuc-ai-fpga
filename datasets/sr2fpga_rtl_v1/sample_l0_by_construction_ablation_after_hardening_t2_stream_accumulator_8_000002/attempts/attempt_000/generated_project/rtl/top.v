module top (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  input wire [7:0] in_data,
  output wire in_ready,
  output wire [7:0] sum
);
  wire skid_out_valid;
  wire [7:0] skid_out_data;
  wire skid_out_ready;

  skid_buffer #(.WIDTH(8)) u_skid (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out_valid(skid_out_valid),
    .out_ready(skid_out_ready),
    .out_data(skid_out_data)
  );

  accumulator_core #(.WIDTH(8)) u_acc (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(skid_out_valid),
    .sample_ready(skid_out_ready),
    .sample(skid_out_data),
    .sum(sum)
  );

endmodule
