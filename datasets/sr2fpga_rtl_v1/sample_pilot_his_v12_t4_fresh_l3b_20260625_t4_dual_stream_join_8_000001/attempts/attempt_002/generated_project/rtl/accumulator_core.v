`timescale 1ns / 1ps

// Accumulator core: adds input to internal register modulo 256
module accumulator_core #(
  parameter DATA_WIDTH = 8
) (
  input  wire                clk,
  input  wire                rst_n,
  input  wire                in_valid,
  output wire                in_ready,
  input  wire [DATA_WIDTH-1:0] in_data,
  output wire                out_valid,
  input  wire                out_ready,
  output wire [DATA_WIDTH-1:0] out_data
);

  reg [DATA_WIDTH-1:0] acc_reg;
  reg acc_valid;

  wire transfer_in = in_valid & in_ready;
  wire transfer_out = acc_valid & out_ready;

  assign in_ready = out_ready | ~acc_valid;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc_reg <= 0;
      acc_valid <= 1'b0;
    end else begin
      if (transfer_out) begin
        acc_valid <= 1'b0;
      end
      if (transfer_in & (transfer_out | ~acc_valid)) begin
        acc_reg <= acc_reg + in_data;
        acc_valid <= 1'b1;
      end
    end
  end

  assign out_valid = acc_valid;
  assign out_data = acc_reg;

endmodule
