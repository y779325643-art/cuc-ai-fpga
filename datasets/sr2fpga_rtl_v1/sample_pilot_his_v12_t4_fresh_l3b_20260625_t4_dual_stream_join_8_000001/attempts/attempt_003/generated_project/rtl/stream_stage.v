`timescale 1ns / 1ps

// Pipeline stage with valid-ready handshake
module stream_stage #(
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

  reg [DATA_WIDTH-1:0] pipe_reg;
  reg pipe_valid;

  wire transfer_in = in_valid & in_ready;
  wire transfer_out = pipe_valid & out_ready;

  assign in_ready = out_ready | ~pipe_valid;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pipe_reg <= 0;
      pipe_valid <= 1'b0;
    end else begin
      if (transfer_out) begin
        pipe_valid <= 1'b0;
      end
      if (transfer_in & (transfer_out | ~pipe_valid)) begin
        pipe_reg <= in_data;
        pipe_valid <= 1'b1;
      end
    end
  end

  assign out_valid = pipe_valid;
  assign out_data = pipe_reg;

endmodule
