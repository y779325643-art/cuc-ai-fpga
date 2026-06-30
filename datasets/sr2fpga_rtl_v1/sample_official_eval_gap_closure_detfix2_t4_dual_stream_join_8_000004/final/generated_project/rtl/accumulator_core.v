module accumulator_core #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire sample_ready,
    input wire [WIDTH-1:0] sample,
    output wire [WIDTH+3:0] sum
);

  reg [WIDTH+3:0] sum_r;

  assign sum = sum_r + ((sample_valid && sample_ready) ? {{4{1'b0}}, sample} : {(WIDTH+4){1'b0}});

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sum_r <= {(WIDTH+4){1'b0}};
    end else if (sample_valid && sample_ready) begin
      sum_r <= sum;
    end
  end

endmodule
