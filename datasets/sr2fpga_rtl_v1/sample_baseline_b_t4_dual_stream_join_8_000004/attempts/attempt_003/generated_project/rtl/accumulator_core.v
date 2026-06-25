module accumulator_core (
  input wire clk,
  input wire rst_n,
  input wire sample_valid,
  input wire [7:0] sample,
  output reg sample_ready,
  output reg sum_valid,
  output reg [7:0] sum,
  input wire sum_ready
);
  reg [7:0] accumulator;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      accumulator <= 8'b0;
      sample_ready <= 1'b1;
      sum_valid <= 1'b0;
    end else begin
      if (sum_ready && sum_valid) begin
        sum_valid <= 1'b0;
        sample_ready <= 1'b1;
      end
      if (sample_valid && sample_ready) begin
        accumulator <= accumulator + sample;
        sum <= accumulator + sample;
        sum_valid <= 1'b1;
        sample_ready <= 1'b0;
      end
    end
  end
endmodule
