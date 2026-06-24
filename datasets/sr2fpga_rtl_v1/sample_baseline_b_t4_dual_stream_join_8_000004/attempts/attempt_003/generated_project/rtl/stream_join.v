module stream_join (
  input wire clk,
  input wire rst_n,
  input wire in0_valid,
  input wire [7:0] in0_data,
  output reg in0_ready,
  input wire in1_valid,
  input wire [7:0] in1_data,
  output reg in1_ready,
  output reg out_valid,
  output reg [7:0] out_data,
  input wire out_ready
);
  reg joined;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      in0_ready <= 1'b1;
      in1_ready <= 1'b1;
      out_valid <= 1'b0;
      joined <= 1'b0;
    end else begin
      if (out_ready && out_valid) begin
        out_valid <= 1'b0;
        joined <= 1'b0;
      end
      if (!joined && in0_valid && in1_valid && in0_ready && in1_ready) begin
        out_data <= in0_data; // or sum? choosing in0_data
        out_valid <= 1'b1;
        in0_ready <= 1'b0;
        in1_ready <= 1'b0;
        joined <= 1'b1;
      end else if (!joined && (!in0_valid || !in1_valid)) begin
        in0_ready <= 1'b1;
        in1_ready <= 1'b1;
      end
      if (out_ready && !out_valid && joined) begin
        out_valid <= 1'b1;
      end
    end
  end
endmodule
