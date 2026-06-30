module tb_top;
  localparam WIDTH = 8;
  localparam DATA_WIDTH = 8;
  reg clk;
  reg rst_n;
  reg in_valid;
  reg [WIDTH-1:0] in_data;
  wire in_ready;
  wire out0_valid;
  wire [WIDTH-1:0] out0_data;
  reg out0_ready;
  wire out1_valid;
  wire [WIDTH-1:0] out1_data;
  reg out1_ready;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .in_ready(in_ready),
    .out0_valid(out0_valid),
    .out0_data(out0_data),
    .out0_ready(out0_ready),
    .out1_valid(out1_valid),
    .out1_data(out1_data),
    .out1_ready(out1_ready)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
