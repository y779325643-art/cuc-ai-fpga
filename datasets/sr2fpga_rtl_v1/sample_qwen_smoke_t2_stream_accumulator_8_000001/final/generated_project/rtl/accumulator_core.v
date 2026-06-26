`timescale 1ns / 1ps
module accumulator_core #(
  parameter WIDTH = 8
) (
  input  wire              clk,
  input  wire              rst_n,
  input  wire              s_valid,
  output wire              s_ready,
  input  wire [WIDTH-1:0]  s_data,
  output wire              m_valid,
  input  wire              m_ready,
  output wire [WIDTH-1:0]  m_data
);

  // Accumulator register (9 bits to handle overflow)
  reg [WIDTH:0] accum_reg;
  
  // Output register
  reg [WIDTH-1:0] out_data_reg;
  reg out_valid_reg;

  // Ready is always asserted since we can accept data every cycle
  assign s_ready = 1'b1;
  assign m_valid = out_valid_reg;
  assign m_data = out_data_reg;

  always @(posedge clk) begin
    if (!rst_n) begin
      accum_reg <= 9'b0;
      out_data_reg <= {WIDTH{1'b0}};
      out_valid_reg <= 1'b0;
    end else begin
      // Update accumulator when input is valid
      if (s_valid) begin
        accum_reg <= accum_reg + {1'b0, s_data};
      end
      
      // Update output register
      out_data_reg <= accum_reg[WIDTH-1:0];
      // Valid follows the accumulator update (after first sample)
      if (s_valid) begin
        out_valid_reg <= 1'b1;
      end else if (m_ready) begin
        out_valid_reg <= 1'b0;
      end
    end
  end

endmodule
