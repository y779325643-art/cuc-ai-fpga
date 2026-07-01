`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg we;
  reg [1:0] addr;
  reg [15:0] wdata;
  wire [15:0] rdata;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .we(we),
    .addr(addr),
    .wdata(wdata),
    .rdata(rdata)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    we = 1'b0;
    addr = 2'd0;
    wdata = 16'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    addr = 2'd2;
    wdata = 16'd99;
    we = 1'b1;
    @(negedge clk);
    we = 1'b0;
    @(negedge clk);
    if (rdata !== 16'd99) begin
      $display("TEST_FAIL expected rdata=99 got %0d", rdata);
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
