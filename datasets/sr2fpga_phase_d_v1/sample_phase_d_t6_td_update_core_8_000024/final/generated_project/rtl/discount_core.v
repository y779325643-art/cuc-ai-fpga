module discount_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] gamma,
    input wire [DATA_WIDTH-1:0] next_value,
    output wire [DATA_WIDTH-1:0] discounted_value
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  wire  [2*DATA_WIDTH-1:0] mult_result;
  wire  [DATA_WIDTH-1:0]   result;
  assign mult_result = gamma * next_value;
  assign result      = mult_result[DATA_WIDTH-1:0];
  assign discounted_value = result;

  always @* begin
    if (mult_result[2*DATA_WIDTH-1:DATA_WIDTH] != 0) begin
    end
  end
  // SR2FPGA_BEHAVIOR_END
endmodule
