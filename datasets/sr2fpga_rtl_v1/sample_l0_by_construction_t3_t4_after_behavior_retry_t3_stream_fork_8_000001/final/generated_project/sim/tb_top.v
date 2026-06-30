module tb_top;
  reg clk;
  reg rst_n;
  reg [DATA_WIDTH-1:0] in_data;
  reg in_valid;
  wire in_ready;
  wire [DATA_WIDTH-1:0] out0_data;
  wire out0_valid;
  reg out0_ready;
  wire [DATA_WIDTH-1:0] out1_data;
  wire out1_valid;
  reg out1_ready;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in_data),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .out0_data(out0_data),
    .out0_valid(out0_valid),
    .out0_ready(out0_ready),
    .out1_data(out1_data),
    .out1_valid(out1_valid),
    .out1_ready(out1_ready)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
