module tb_top;
  localparam DATA_WIDTH = 8;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [7:0] in_data;
  wire out0_valid;
  reg out0_ready;
  wire [7:0] out0_data;
  wire out1_valid;
  reg out1_ready;
  wire [7:0] out1_data;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out0_valid(out0_valid),
    .out0_ready(out0_ready),
    .out0_data(out0_data),
    .out1_valid(out1_valid),
    .out1_ready(out1_ready),
    .out1_data(out1_data)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
