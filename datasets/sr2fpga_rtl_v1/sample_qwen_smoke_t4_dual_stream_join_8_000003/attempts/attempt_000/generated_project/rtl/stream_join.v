`timescale 1ns / 1ps
module stream_join #(
  parameter DATA_WIDTH = 8
) (
  input  wire                    clk,
  input  wire                    rst_n,
  input  wire [DATA_WIDTH-1:0]   in0_data,
  input  wire                    in0_valid,
  output wire                    in0_ready,
  input  wire [DATA_WIDTH-1:0]   in1_data,
  input  wire                    in1_valid,
  output wire                    in1_ready,
  output wire [DATA_WIDTH-1:0]   out_data,
  output wire                    out_valid,
  input  wire                    out_ready
);

  reg [DATA_WIDTH-1:0] joined_data_reg;
  reg                  valid_reg;
  
  // Join operation: add the two input values
  assign joined_data_reg = in0_data + in1_data;
  
  // Output is valid when both inputs are valid
  assign out_data = joined_data_reg;
  assign out_valid = valid_reg;
  assign in0_ready = out_ready & ~valid_reg;
  assign in1_ready = out_ready & ~valid_reg;
  
  always @(posedge clk) begin
    if (!rst_n) begin
      valid_reg <= 0;
    end else begin
      if (out_ready) begin
        // If output is ready, consume the current valid data
        if (in0_valid & in1_valid) begin
          // Both inputs are valid, capture the joined data
          valid_reg <= 1;
        end else begin
          // Either output was consumed or we're waiting for both inputs
          valid_reg <= (in0_valid & in1_valid) ? 1 : 0;
        end
      end else if (in0_valid & in1_valid) begin
        // Output not ready but both inputs are valid, store for next cycle
        valid_reg <= 1;
      end
    end
  end

endmodule
