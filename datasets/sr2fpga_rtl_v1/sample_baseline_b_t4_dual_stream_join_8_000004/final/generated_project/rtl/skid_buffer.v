module skid_buffer (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  input wire [7:0] in_data,
  output reg in_ready,
  output reg out_valid,
  output reg [7:0] out_data,
  input wire out_ready
);
  reg [7:0] skid_data;
  reg skid_valid;
  reg has_space;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      in_ready <= 1'b1;
      out_valid <= 1'b0;
      skid_valid <= 1'b0;
      has_space <= 1'b1;
    end else begin
      if (out_ready && out_valid) begin
        out_valid <= 1'b0;
        if (skid_valid) begin
          out_data <= skid_data;
          out_valid <= 1'b1;
          skid_valid <= 1'b0;
          in_ready <= 1'b1;
        end else begin
          in_ready <= 1'b1;
        end
      end
      if (in_valid && in_ready) begin
        if (out_valid && !out_ready) begin
          skid_data <= in_data;
          skid_valid <= 1'b1;
          in_ready <= 1'b0;
        end else begin
          out_data <= in_data;
          out_valid <= 1'b1;
          in_ready <= 1'b0;
        end
      end
    end
  end
endmodule
