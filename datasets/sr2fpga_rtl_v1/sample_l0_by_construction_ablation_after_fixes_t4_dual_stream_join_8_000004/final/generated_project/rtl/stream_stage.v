`timescale 1ns / 1ps
module stream_stage #(parameter WIDTH = 16) (
  input clk,
  input rst_n,
  input in_valid,
  input [WIDTH-1:0] in_data,
  output in_ready,
  output out_valid,
  output [WIDTH-1:0] out_data,
  input out_ready
);

  reg [WIDTH-1:0] data_r;
  reg valid_r;

  assign in_ready = !valid_r || out_ready;
  assign out_valid = valid_r;
  assign out_data = data_r;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_r <= 0;
    end else begin
      if (out_ready || !valid_r) begin
        if (in_valid) begin
          data_r <= in_data;
          valid_r <= 1;
        end else begin
          valid_r <= 0;
        end
      end
    end
  end

endmodule
