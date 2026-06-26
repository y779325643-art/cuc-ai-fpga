`timescale 1ns/1ps
module skid_buffer #(
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

  reg [WIDTH-1:0] buffer_reg;
  reg buffer_full;
  
  // Output valid is true if there's data in buffer OR input is valid
  assign m_valid = s_valid | buffer_full;
  // Input is ready if we don't have full buffer OR output is ready
  assign s_ready = (~buffer_full) | m_ready;
  
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      buffer_full <= 1'b0;
      buffer_reg <= {WIDTH{1'b0}};
    end else begin
      if (s_valid & s_ready) begin
        // If input is consumed, move it to buffer if output not ready
        if (!m_ready) begin
          buffer_reg <= s_data;
          buffer_full <= 1'b1;
        end
      end
      
      if (m_ready & buffer_full) begin
        // If output consumes from buffer
        buffer_full <= 1'b0;
      end
    end
  end
  
  // Output data comes from input if available and output ready,
  // otherwise from buffer
  assign m_data = buffer_full ? buffer_reg : s_data;

endmodule
