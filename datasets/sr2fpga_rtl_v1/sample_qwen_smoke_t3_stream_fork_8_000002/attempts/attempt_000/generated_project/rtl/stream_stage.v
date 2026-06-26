`timescale 1ns/1ps
module stream_stage #(
  parameter WIDTH = 8
) (
  input  wire         clk,
  input  wire         rst_n,
  input  wire         s_valid,
  output wire         s_ready,
  input  wire [WIDTH-1:0] s_data,
  output wire         m_valid,
  input  wire         m_ready,
  output wire [WIDTH-1:0] m_data
);

  reg [WIDTH-1:0] data_reg;
  reg valid_reg;
  
  assign s_ready = ~valid_reg | m_ready;
  assign m_valid = valid_reg;
  assign m_data = data_reg;
  
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_reg <= 1'b0;
      data_reg <= {WIDTH{1'b0}};
    end else begin
      if (s_valid & s_ready) begin
        data_reg <= s_data;
        valid_reg <= 1'b1;
      end
      
      if (m_ready & valid_reg) begin
        valid_reg <= 1'b0;
      end
    end
  end

endmodule
