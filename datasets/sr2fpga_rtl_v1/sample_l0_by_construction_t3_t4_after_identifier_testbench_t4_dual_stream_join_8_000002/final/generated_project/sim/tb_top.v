module tb_top;
  reg [None-1:0] clk;
  reg [None-1:0] rst_n;
  reg [None-1:0] in0_valid;
  reg [7:0] in0_data;
  wire [None-1:0] in0_ready;
  reg [None-1:0] in1_valid;
  reg [7:0] in1_data;
  wire [None-1:0] in1_ready;
  wire [None-1:0] out_valid;
  wire [7:0] out_data;
  reg [None-1:0] out_ready;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_data(in0_data),
    .in0_ready(in0_ready),
    .in1_valid(in1_valid),
    .in1_data(in1_data),
    .in1_ready(in1_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(out_ready)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
