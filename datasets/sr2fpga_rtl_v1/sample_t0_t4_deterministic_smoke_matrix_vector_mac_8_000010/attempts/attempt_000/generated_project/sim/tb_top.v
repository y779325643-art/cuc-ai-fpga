`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg start;
  wire busy;
  wire done;
  wire [11:0] result;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .start(start),
    .busy(busy),
    .done(done),
    .result(result)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    start = 1'b0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    start = 1'b1;
    @(negedge clk);
    start = 1'b0;
    while (done !== 1'b1) begin
      @(posedge clk);
    end
    #1;
    if (busy !== 1'b0) begin
      $display("TEST_FAIL busy did not clear");
      $finish;
    end
    if (result !== 12'd17) begin
      $display("TEST_FAIL expected result=17 got %0d", result);
      $finish;
    end
    @(posedge clk);
    #1;
    if (done !== 1'b0) begin
      $display("TEST_FAIL done was not one cycle");
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
