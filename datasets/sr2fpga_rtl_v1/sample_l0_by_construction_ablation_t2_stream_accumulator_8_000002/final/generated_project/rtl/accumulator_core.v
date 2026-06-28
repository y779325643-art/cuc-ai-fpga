module accumulator_core (
  input clk,
  input rst_n,
  input sample_valid,
  input [7:0] sample,
  output sample_ready,
  output reg [7:0] sum
);

  assign sample_ready = 1'b1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sum <= 8'd0;
    end else if (sample_valid && sample_ready) begin
      sum <= sum + sample;
    end
  end

endmodule
