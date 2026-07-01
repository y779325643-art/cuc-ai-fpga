`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in0_valid;
  wire in0_ready;
  reg [7:0] in0_data;
  reg in1_valid;
  wire in1_ready;
  reg [7:0] in1_data;
  wire out_valid;
  reg out_ready;
  wire [11:0] out_data;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_ready(in0_ready),
    .in0_data(in0_data),
    .in1_valid(in1_valid),
    .in1_ready(in1_ready),
    .in1_data(in1_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    in0_valid = 1'b0;
    in0_data = 8'd0;
    in1_valid = 1'b0;
    in1_data = 8'd0;
    out_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    in0_valid = 1'b1;
    in0_data = 8'd3;
    in1_valid = 1'b1;
    in1_data = 8'd5;
    @(negedge clk);
    in0_valid = 1'b0;
    in1_valid = 1'b0;
    in0_data = 8'd0;
    in1_data = 8'd0;
    wait_cycles = 0;
    while (out_valid !== 1'b1 && wait_cycles < 8) begin
      @(posedge clk);
      #1;
      wait_cycles = wait_cycles + 1;
    end
    #1;

    if (out_valid !== 1'b1) begin
      $display("TEST_FAIL joined output not valid");
      $finish;
    end
    if (out_data !== 12'd8) begin
      $display("TEST_FAIL expected joined sum=%0d got %0d", 8, out_data);
      $finish;
    end
    if (in0_ready !== 1'b1 || in1_ready !== 1'b1) begin
      $display("TEST_FAIL joined inputs not ready");
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
