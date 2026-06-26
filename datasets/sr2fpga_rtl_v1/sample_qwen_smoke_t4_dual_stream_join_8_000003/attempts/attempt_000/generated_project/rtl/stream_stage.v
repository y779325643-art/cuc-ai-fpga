`timescale 1ns / 1ps
module stream_stage #(
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

  reg [DATA_WIDTH-1:0] data_reg;
  reg                  valid_reg;
  
  // Output assignments
  assign out_data = data_reg;
  assign out_valid = valid_reg;
  assign in_ready = ~valid_reg | out_ready;
  
  always @(posedge clk) begin
    if (!rst_n) begin
      data_reg <= 0;
      valid_reg <= 0;
    end else begin
      if (out_ready) begin
        // Output consumed, can accept new input
        if (in_valid) begin
          data_reg <= in_data;
          valid_reg <= 1;
        end else begin
          valid_reg <= 0;
        end
      end else if (in_valid & ~valid_reg) begin
        // Store new data if not already stored
        data_reg <= in_data;
        valid_reg <= 1;
      end
    end
  end

endmodule
