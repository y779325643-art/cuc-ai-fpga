`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg wr_en;
  reg rd_en;
  reg [3:0] din;
  wire [3:0] dout;
  wire full;
  wire empty;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .wr_en(wr_en),
    .rd_en(rd_en),
    .din(din),
    .dout(dout),
    .full(full),
    .empty(empty)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    wr_en = 1'b0;
    rd_en = 1'b0;
    din = 4'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    din = 4'd42;
    wr_en = 1'b1;
    @(negedge clk);
    wr_en = 1'b0;
    if (empty !== 1'b0) begin
      $display("TEST_FAIL fifo should not be empty after write");
      $finish;
    end

    rd_en = 1'b1;
    @(negedge clk);
    rd_en = 1'b0;
    @(negedge clk);
    if (dout !== 4'd42) begin
      $display("TEST_FAIL expected dout=42 got %0d", dout);
      $finish;
    end
    if (empty !== 1'b1) begin
      $display("TEST_FAIL fifo should be empty after read");
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endmodule
