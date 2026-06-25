`timescale 1ns/1ps
module tb;
  reg clk, rst_n;
  reg [7:0] in0_data, in1_data;
  reg in0_valid, in1_valid;
  wire in0_ready, in1_ready;
  wire [7:0] out_data;
  wire out_valid;
  reg out_ready;

  top #(.DATA_WIDTH(8)) dut (
    .clk(clk), .rst_n(rst_n),
    .in0_data(in0_data), .in0_valid(in0_valid), .in0_ready(in0_ready),
    .in1_data(in1_data), .in1_valid(in1_valid), .in1_ready(in1_ready),
    .out_data(out_data), .out_valid(out_valid), .out_ready(out_ready)
  );

  always #5 clk = ~clk;

  initial begin
    clk = 0;
    rst_n = 0;
    in0_valid = 0;
    in1_valid = 0;
    out_ready = 0;
    in0_data = 0;
    in1_data = 0;
    #10;
    rst_n = 1;
    #10;
    out_ready = 1;
    in0_data = 8'd1;
    in1_data = 8'd2;
    in0_valid = 1;
    in1_valid = 1;

    integer i;
    reg [7:0] expected;
    integer timeout = 0;
    for (i = 0; i < 4; i = i + 1) begin
      expected = 3 * (i + 1);
      wait(out_valid);
      @(posedge clk) #1;
      if (out_data !== expected) begin
        $display("TEST_FAIL: output mismatch at transfer %0d: expected %0d, got %0d", i, expected, out_data);
        $finish;
      end
      @(posedge clk);
    end
    $display("TEST_PASS");
    $finish;
  end

  initial begin
    #1000;
    $display("TEST_FAIL: timeout");
    $finish;
  end
endmodule
