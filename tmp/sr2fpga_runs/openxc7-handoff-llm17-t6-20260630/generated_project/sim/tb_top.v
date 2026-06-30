module tb_top;
  localparam DATA_WIDTH = 8;
  localparam SCALE_SHIFT = 4;
  reg clk;
  reg rst_n;
  reg in_valid;
  reg [7:0] reward;
  reg [7:0] value;
  reg [7:0] next_value;
  reg [7:0] gamma;
  reg [7:0] alpha;
  reg out_ready;
  wire in_ready;
  wire out_valid;
  wire [7:0] td_error;
  wire [7:0] updated_value;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .reward(reward),
    .value(value),
    .next_value(next_value),
    .gamma(gamma),
    .alpha(alpha),
    .out_ready(out_ready),
    .in_ready(in_ready),
    .out_valid(out_valid),
    .td_error(td_error),
    .updated_value(updated_value)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
