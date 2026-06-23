module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [11:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [11:0] out_data
);

  wire skid_valid;
  wire skid_ready;
  wire [11:0] skid_data;

  skid_buffer #(
    .WIDTH(12)
  ) u_skid_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out_valid(skid_valid),
    .out_ready(skid_ready),
    .out_data(skid_data)
  );

  stream_stage #(
    .WIDTH(12)
  ) u_stream_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(skid_valid),
    .in_ready(skid_ready),
    .in_data(skid_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
  );

endmodule
