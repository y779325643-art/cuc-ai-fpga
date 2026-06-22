`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg start;
  reg [7:0] tx_data;
  reg miso;
  wire [7:0] rx_data;
  wire busy;
  wire done;
  wire sclk;
  wire mosi;
  wire cs_n;

  reg [7:0] miso_pattern;
  integer miso_bit;
  integer sclk_edge_count;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .start(start),
    .tx_data(tx_data),
    .miso(miso),
    .rx_data(rx_data),
    .busy(busy),
    .done(done),
    .sclk(sclk),
    .mosi(mosi),
    .cs_n(cs_n)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  always @(negedge sclk or posedge cs_n) begin
    if (cs_n) begin
      miso_bit = 7;
      miso = miso_pattern[7];
    end else if (miso_bit > 0) begin
      miso_bit = miso_bit - 1;
      miso = miso_pattern[miso_bit];
    end
  end

  always @(posedge sclk) begin
    if (!cs_n) begin
      sclk_edge_count = sclk_edge_count + 1;
    end
  end

  initial begin
    rst_n = 1'b0;
    start = 1'b0;
    tx_data = 8'd0;
    miso_pattern = 8'h3C;
    miso_bit = 7;
    sclk_edge_count = 0;
    miso = miso_pattern[7];
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    tx_data = 8'hA5;
    start = 1'b1;
    @(negedge clk);
    start = 1'b0;
    #1;
    if (busy !== 1'b1 || cs_n !== 1'b0) begin
      $display("TEST_FAIL transfer did not start");
      $finish;
    end
    if (mosi !== 1'b1) begin
      $display("TEST_FAIL expected first MOSI bit 1 got %0b", mosi);
      $finish;
    end

    while (done !== 1'b1) begin
      @(posedge clk);
    end
    #1;
    if (cs_n !== 1'b1) begin
      $display("TEST_FAIL cs_n was not released");
      $finish;
    end
    if (sclk_edge_count != 8) begin
      $display("TEST_FAIL expected 8 SCLK rising edges got %0d", sclk_edge_count);
      $finish;
    end
    if (rx_data !== 8'h3C) begin
      $display("TEST_FAIL expected rx_data=3c got %02h", rx_data);
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
endmodule
