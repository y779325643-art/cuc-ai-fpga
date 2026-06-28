`timescale 1ns / 1ps
module skid_buffer #(parameter WIDTH = 8) (
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
  reg [WIDTH-1:0] skid_data;
  reg valid_r;
  reg skid_valid;

  assign in_ready = !valid_r || out_ready;
  assign out_valid = valid_r;
  assign out_data = data_r;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_r <= 1'b0;
      skid_valid <= 1'b0;
      data_r <= {WIDTH{1'b0}};
      skid_data <= {WIDTH{1'b0}};
    end else begin
      // Handle output consumption and skid movement
      if (out_ready) begin
        if (skid_valid) begin
          data_r <= skid_data;
          valid_r <= 1'b1;
          skid_valid <= 1'b0;
        end else if (valid_r) begin
          valid_r <= 1'b0;
        end
      end
      // Handle input acceptance
      if (in_ready && in_valid) begin
        if (!valid_r && !skid_valid) begin
          data_r <= in_data;
          valid_r <= 1'b1;
        end else if (!skid_valid) begin
          skid_data <= in_data;
          skid_valid <= 1'b1;
        end
      end
    end
  end

endmodule
