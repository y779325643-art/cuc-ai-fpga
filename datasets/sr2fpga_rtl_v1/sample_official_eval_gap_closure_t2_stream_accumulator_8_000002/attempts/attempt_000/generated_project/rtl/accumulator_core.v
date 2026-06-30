module accumulator_core #(
    parameter WIDTH = 8,
    parameter SUM_WIDTH = 12
) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    output wire sample_ready,
    input wire [WIDTH-1:0] sample,
    output reg [SUM_WIDTH-1:0] sum
);

  assign sample_ready = 1'b1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sum <= {SUM_WIDTH{1'b0}};
    end else if (sample_valid) begin
      sum <= sum + {{(SUM_WIDTH-WIDTH){1'b0}}, sample};
    end
  end

endmodule
