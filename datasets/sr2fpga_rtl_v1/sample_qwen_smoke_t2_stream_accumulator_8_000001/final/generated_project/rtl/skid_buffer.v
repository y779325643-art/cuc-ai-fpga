`timescale 1ns / 1ps
module skid_buffer #(
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

  // Skid buffer storage
  reg [WIDTH-1:0] buffer_data;
  reg             buffer_valid;

  // Output assignment
  assign s_ready = m_ready | ~buffer_valid;
  assign m_valid = buffer_valid | s_valid;
  assign m_data = buffer_valid ? buffer_data : s_data;

  always @(posedge clk) begin
    if (!rst_n) begin
      buffer_data <= {WIDTH{1'b0}};
      buffer_valid <= 1'b0;
    end else begin
      if (m_ready && buffer_valid) begin
        // Output consumed, replace with new data if available
        if (s_valid) begin
          buffer_data <= s_data;
        end else begin
          buffer_valid <= 1'b0;
        end
      end else if (m_ready && !buffer_valid && s_valid) begin
        // No buffered data, but new data available
        buffer_data <= s_data;
        buffer_valid <= 1'b1;
      end else if (!m_ready && s_valid && !buffer_valid) begin
        // Backpressure, store incoming data
        buffer_data <= s_data;
        buffer_valid <= 1'b1;
      end
    end
  end

endmodule
