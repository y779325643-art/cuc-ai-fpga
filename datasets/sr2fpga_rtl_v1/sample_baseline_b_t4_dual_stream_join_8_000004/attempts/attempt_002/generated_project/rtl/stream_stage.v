module stream_stage (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  input wire [7:0] in_data,
  output reg in_ready,
  output reg out_valid,
  output reg [7:0] out_data,
  input wire out_ready
);
  reg valid_d;
  reg [7:0] data_d;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      in_ready <= 1'b1;
      out_valid <= 1'b0;
      valid_d <= 1'b0;
    end else begin
      if (out_ready && out_valid) begin
        out_valid <= valid_d;
        out_data <= data_d;
        if (valid_d) begin
          in_ready <= 1'b1;
        end else begin
          in_ready <= 1'b1;
        end
      end
      if (in_valid && in_ready) begin
        if (out_valid && !out_ready) begin
          data_d <= in_data;
          valid_d <= 1'b1;
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
