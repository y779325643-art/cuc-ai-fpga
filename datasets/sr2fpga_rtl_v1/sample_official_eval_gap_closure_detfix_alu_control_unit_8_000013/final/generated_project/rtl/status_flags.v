module status_flags #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire valid,
    input wire [WIDTH-1:0] alu_result,
    input wire alu_carry,
    output reg result_valid,
    output reg [WIDTH-1:0] result,
    output reg zero,
    output reg carry,
    output reg negative
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      result_valid <= 1'b0;
      result <= {WIDTH{1'b0}};
      zero <= 1'b0;
      carry <= 1'b0;
      negative <= 1'b0;
    end else if (valid) begin
      result_valid <= 1'b1;
      result <= alu_result;
      zero <= (alu_result == {WIDTH{1'b0}});
      carry <= alu_carry;
      negative <= alu_result[WIDTH-1];
    end else begin
      result_valid <= 1'b0;
    end
  end

endmodule
