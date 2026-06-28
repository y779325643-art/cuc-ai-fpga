module accumulator_core #(parameter WIDTH=8) (
  input wire clk,
  input wire rst_n,
  input wire sample_valid,
  output reg sample_ready,
  input wire [WIDTH-1:0] sample,
  output reg [WIDTH-1:0] sum
);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sum <= 0;
      sample_ready <= 1'b0;
    end else begin
      sample_ready <= 1'b1;
      if (sample_valid && sample_ready) begin
        sum <= sum + sample;
      end
    end
  end
endmodule
