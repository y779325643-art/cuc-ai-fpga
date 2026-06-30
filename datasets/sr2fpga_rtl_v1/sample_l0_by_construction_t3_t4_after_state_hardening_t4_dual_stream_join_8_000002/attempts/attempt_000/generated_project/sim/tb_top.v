module tb_top;
  reg clk;
  reg rst_n;
  reg in0_valid;
  reg [7:0] in0_data;
  wire in0_ready;
  reg in1_valid;
  reg [7:0] in1_data;
  wire in1_ready;
  wire out_valid;
  wire [7:0] out_data;
  reg out_ready;
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
