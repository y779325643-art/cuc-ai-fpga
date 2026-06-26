`timescale 1ns / 1ps
module accumulator_core #(
  parameter DATA_WIDTH = 8
) (
  input  wire                    clk,
  input  wire                    rst_n,
  input  wire [DATA_WIDTH-1:0]   in_data,
  input  wire                    in_valid,
  output wire                    in_ready,
  output wire [DATA_WIDTH-1:0]   out_data,
  output wire                    out_valid,
  input  wire                    out_ready
);

  reg [DATA_WIDTH-1:0] accum_reg;
  reg                  valid_reg;
  
  // Output assignments
  assign out_data = accum_reg;
  assign out_valid = valid_reg;
  assign in_ready = out_ready;  // Simple backpressure
  
  always @(posedge clk) begin
    if (!rst_n) begin
      accum_reg <= 0;
      valid_reg <= 0;
    end else begin
      if (in_valid & in_ready) begin
        // Update accumulator when input is valid and ready
        accum_reg <= (accum_reg + in_data) % 256;
        valid_reg <= 1;
      end else if (out_ready) begin
        // Clear valid flag when output is consumed
        valid_reg <= 0;
      end
    end
  end

endmodule
