`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg we;
  reg [1:0] addr;
  reg [7:0] wdata;
  wire [7:0] rdata;

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
    wdata = 8'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    // Write-first behavior is not allowed: the synchronous read returns
    // the old word on the write edge.
    @(negedge clk);
    addr = 2'd0;
    wdata = 8'd17;
    we = 1'b1;
    @(negedge clk);
    if (rdata !== 8'd0) begin
      $display("TEST_FAIL ram read_during_write expected=0 actual=%0d", rdata);
      $finish;
    end
    we = 1'b0;
    @(negedge clk);
    if (rdata !== 8'd17) begin
      $display("TEST_FAIL ram sync_read expected=17 actual=%0d", rdata);
      $finish;
    end

    // Changing the address must not change rdata until a clock edge.
    addr = 2'd1;
    #1;
    if (rdata !== 8'd17) begin
      $display("TEST_FAIL ram async_read_detected expected=17 actual=%0d", rdata);
      $finish;
    end
    @(negedge clk);
    if (rdata !== 8'd0) begin
      $display("TEST_FAIL ram address1 expected=0 actual=%0d", rdata);
      $finish;
    end

    // Address 2 must be independent from address 0.
    @(negedge clk);
    addr = 2'd2;
    wdata = 8'd99;
    we = 1'b1;
    @(negedge clk);
    we = 1'b0;
    @(negedge clk);
    if (rdata !== 8'd99) begin
      $display("TEST_FAIL ram address2 expected=99 actual=%0d", rdata);
      $finish;
    end
    addr = 2'd0;
    @(negedge clk);
    if (rdata !== 8'd17) begin
      $display("TEST_FAIL ram address0_preserved expected=17 actual=%0d", rdata);
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
