`timescale 1ns / 1ps
module stream_join #(parameter WIDTH = 8) (
  input clk,
  input rst_n,
  input in0_valid,
  input [WIDTH-1:0] in0_data,
  output in0_ready,
  input in1_valid,
  input [WIDTH-1:0] in1_data,
  output in1_ready,
  output out_valid,
  output [2*WIDTH-1:0] out_data,
  input out_ready
);

  reg out_valid_r;
  reg [2*WIDTH-1:0] out_data_r;

  assign in0_ready = ((!out_valid_r) || out_ready) && in1_valid;
  assign in1_ready = ((!out_valid_r) || out_ready) && in0_valid;
  assign out_valid = out_valid_r;
  assign out_data = out_data_r;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid_r <= 1'b0;
    end else begin
      if (!out_valid_r || out_ready) begin
        if (in0_valid && in1_valid) begin
          out_valid_r <= 1'b1;
          out_data_r <= {in0_data, in1_data};
        end else if (out_ready && out_valid_r) begin
          out_valid_r <= 1'b0;
        end
      end
    end
  end

endmodule
