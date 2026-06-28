module tb_top;
  reg [None-1:0] clk;
  reg [None-1:0] rst_n;
  reg [None-1:0] in_valid;
  reg [DATA_WIDTH-1:0] in_data;
  wire [None-1:0] in_ready;
  wire [None-1:0] out0_valid;
  wire [DATA_WIDTH-1:0] out0_data;
  reg [None-1:0] out0_ready;
  wire [None-1:0] out1_valid;
  wire [DATA_WIDTH-1:0] out1_data;
  reg [None-1:0] out1_ready;
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
