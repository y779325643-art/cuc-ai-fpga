`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg start;
  reg [7:0] data;
  wire tx;
  wire busy;
  wire done;
  reg [7:0] expected_bits;
  integer i;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .start(start),
    .data(data),
    .tx(tx),
    .busy(busy),
    .done(done)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    start = 1'b0;
    data = 8'd0;
    expected_bits = 8'hA5;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    data = 8'hA5;
    start = 1'b1;
    @(negedge clk);
    start = 1'b0;
    #1;
    if (tx !== 1'b0) begin
      $display("TEST_FAIL start bit expected 0 got %0b", tx);
      $finish;
    end
    if (busy !== 1'b1) begin
      $display("TEST_FAIL busy was not asserted");
      $finish;
    end

    for (i = 0; i < 8; i = i + 1) begin
      repeat (4) @(posedge clk);
      #1;
      if (tx !== expected_bits[i]) begin
        $display(
          "TEST_FAIL data bit %0d expected %0b got %0b",
          i,
          expected_bits[i],
          tx
        );
        $finish;
      end
    end

    repeat (4) @(posedge clk);
    #1;
    if (tx !== 1'b1) begin
      $display("TEST_FAIL stop bit expected 1 got %0b", tx);
      $finish;
    end

    repeat (4) @(posedge clk);
    #1;
    if (done !== 1'b1) begin
      $display("TEST_FAIL done was not asserted");
      $finish;
    end
    if (busy !== 1'b0) begin
      $display("TEST_FAIL busy did not clear");
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
