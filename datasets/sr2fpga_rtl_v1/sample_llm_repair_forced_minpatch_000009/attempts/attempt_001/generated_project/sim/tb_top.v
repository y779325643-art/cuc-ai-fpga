`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg start;
  wire done;
  wire [2:0] state_value;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .start(start),
    .done(done),
    .state_value(state_value)
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
    repeat (5) @(posedge clk);
    if (done !== 1'b1) begin
      $display("TEST_FAIL fsm did not reach done");
      $finish;
    end
    @(negedge clk);
    start = 1'b0;
    repeat (2) @(posedge clk);
    if (done !== 1'b0) begin
      $display("TEST_FAIL fsm did not return to idle");
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endmodule
