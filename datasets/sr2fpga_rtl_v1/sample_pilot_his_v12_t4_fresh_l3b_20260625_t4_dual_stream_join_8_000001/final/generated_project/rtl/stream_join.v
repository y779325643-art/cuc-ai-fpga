`timescale 1ns / 1ps

// Stream join: waits for both inputs valid, then outputs sum modulo 256
module stream_join #(
  parameter DATA_WIDTH = 8
) (
  input  wire                clk,
  input  wire                rst_n,
  input  wire                in0_valid,
  output wire                in0_ready,
  input  wire [DATA_WIDTH-1:0] in0_data,
  input  wire                in1_valid,
  output wire                in1_ready,
  input  wire [DATA_WIDTH-1:0] in1_data,
  output wire                out_valid,
  input  wire                out_ready,
  output wire [DATA_WIDTH-1:0] out_data
);

  // Simple implementation: combinational sum when both valid
  assign in0_ready = out_ready | ~out_valid;
  assign in1_ready = out_ready | ~out_valid;
  // Need registered output for proper handshake with backpressure
  reg [DATA_WIDTH-1:0] sum_reg;
  reg sum_valid;

  wire both_valid = in0_valid & in1_valid;
  wire transfer = sum_valid & out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sum_valid <= 1'b0;
      sum_reg <= 0;
    end else begin
      if (transfer) begin
        sum_valid <= 1'b0;
      end
      if (both_valid & (transfer | ~sum_valid)) begin
        sum_valid <= 1'b1;
        sum_reg <= in0_data + in1_data;
      end
    end
  end

  assign out_valid = sum_valid;
  assign out_data = sum_reg;

endmodule
