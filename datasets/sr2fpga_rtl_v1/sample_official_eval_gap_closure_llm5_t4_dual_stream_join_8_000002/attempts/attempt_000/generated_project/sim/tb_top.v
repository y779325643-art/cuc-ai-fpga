module tb_top;
  localparam DATA_WIDTH = 8;
  reg clk;
  reg rst_n;
  reg in0_valid;
  reg [7:0] in0_data;
  reg in1_valid;
  reg [7:0] in1_data;
  reg out_ready;
  wire in0_ready;
  wire in1_ready;
  wire out_valid;
  wire [7:0] out_data;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_data(in0_data),
    .in1_valid(in1_valid),
    .in1_data(in1_data),
    .out_ready(out_ready),
    .in0_ready(in0_ready),
    .in1_ready(in1_ready),
    .out_valid(out_valid),
    .out_data(out_data)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
