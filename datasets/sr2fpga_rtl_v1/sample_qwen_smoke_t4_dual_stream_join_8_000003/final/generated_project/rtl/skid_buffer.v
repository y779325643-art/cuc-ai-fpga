`timescale 1ns / 1ps
module skid_buffer #(
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

  reg [DATA_WIDTH-1:0] buffer_reg;
  reg                  full_reg;
  
  // Output assignment
  assign out_data = full_reg ? buffer_reg : in_data;
  assign out_valid = in_valid | full_reg;
  assign in_ready = (~full_reg) & out_ready;
  
  always @(posedge clk) begin
    if (!rst_n) begin
      buffer_reg <= 0;
      full_reg <= 0;
    end else begin
      if (in_valid & ~in_ready) begin
        // Input was valid but not consumed, store it
        buffer_reg <= in_data;
        full_reg <= 1;
      end else if (out_ready & full_reg) begin
        // Output consumed the buffered data
        full_reg <= 0;
      end
    end
  end

endmodule
