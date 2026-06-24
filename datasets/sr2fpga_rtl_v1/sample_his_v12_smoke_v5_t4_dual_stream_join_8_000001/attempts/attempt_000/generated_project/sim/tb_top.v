module tb_top;

reg clk, reset_n;
reg in0_valid, in1_valid;
reg [7:0] in0_data, in1_data;
wire in0_ready, in1_ready;
wire out_valid;
wire [7:0] out_data;
reg out_ready;

top dut (
  .clk(clk), .reset_n(reset_n),
  .in0_valid(in0_valid), .in0_data(in0_data), .in0_ready(in0_ready),
  .in1_valid(in1_valid), .in1_data(in1_data), .in1_ready(in1_ready),
  .out_valid(out_valid), .out_data(out_data), .out_ready(out_ready)
);

always #5 clk = ~clk;

initial begin
  $dumpfile("tb_top.vcd");
  $dumpvars(0, tb_top);
  clk = 0;
  reset_n = 0;
  in0_valid = 0; in0_data = 0;
  in1_valid = 0; in1_data = 0;
  out_ready = 1;
  #20 reset_n = 1;
  #10;
  // First pair
  in0_data = 8'd1; in0_valid = 1;
  in1_data = 8'd2; in1_valid = 1;
  #10;
  in0_valid = 0; in1_valid = 0;
  #30;
  // Second pair
  in0_data = 8'd3; in0_valid = 1;
  in1_data = 8'd4; in1_valid = 1;
  #10;
  in0_valid = 0; in1_valid = 0;
  #50;
  // Check output
  if (out_data == 8'd7) begin
    $display("TEST_PASS");
  end else begin
    $display("TEST_FAIL");
  end
  $finish;
end

endmodule
