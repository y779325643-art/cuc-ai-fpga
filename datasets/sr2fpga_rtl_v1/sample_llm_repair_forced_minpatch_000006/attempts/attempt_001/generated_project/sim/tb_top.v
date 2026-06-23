`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg en;
  wire [11:0] count;

  top dut (
    .clk(clk),
    .reset_n(rst_n),
    .en(en),
    .count(count)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    en = 1'b0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;
    en = 1'b1;
    repeat (4) @(posedge clk);
    if (count !== 12'd4) begin
      $display("TEST_FAIL expected count=4 got %0d", count);
      $finish;
    end
    en = 1'b0;
    repeat (2) @(posedge clk);
    if (count !== 12'd4) begin
      $display("TEST_FAIL hold failed got %0d", count);
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endmodule
