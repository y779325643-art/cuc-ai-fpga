`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg wr_en;
  reg rd_en;
  reg [7:0] din;
  wire [7:0] dout;
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

  task write_word;
    input [7:0] value;
    begin
      @(negedge clk);
      din = value;
      wr_en = 1'b1;
      @(negedge clk);
      wr_en = 1'b0;
      #1;
    end
  endtask

  task read_expect;
    input [7:0] expected;
    begin
      @(negedge clk);
      rd_en = 1'b1;
      @(negedge clk);
      rd_en = 1'b0;
      #1;
      if (dout !== expected) begin
        $display("TEST_FAIL expected dout=%0d got %0d", expected, dout);
        $finish;
      end
    end
  endtask

  initial begin
    rst_n = 1'b0;
    wr_en = 1'b0;
    rd_en = 1'b0;
    din = 8'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    write_word(8'd10);
    write_word(8'd11);
    write_word(8'd12);
    write_word(8'd13);
    if (full !== 1'b1) begin
      $display("TEST_FAIL fifo should be full after four writes");
      $finish;
    end

    write_word(8'd99);
    @(negedge clk);
    rd_en = 1'b1;
    @(negedge clk);
    rd_en = 1'b0;
    #1;
    if (dout !== 8'd10) begin
      $display("TEST_FAIL overflow guard changed stored data");
      $finish;
    end
    read_expect(8'd11);
    read_expect(8'd12);
    read_expect(8'd13);

    if (empty !== 1'b1) begin
      $display("TEST_FAIL fifo should be empty after four reads");
      $finish;
    end
    @(negedge clk);
    rd_en = 1'b1;
    @(negedge clk);
    rd_en = 1'b0;
    write_word(8'd77);
    @(negedge clk);
    rd_en = 1'b1;
    @(negedge clk);
    rd_en = 1'b0;
    #1;
    if (dout !== 8'd77) begin
      $display("TEST_FAIL underflow guard advanced read pointer");
      $finish;
    end

    write_word(8'd21);
    @(negedge clk);
    din = 8'd22;
    wr_en = 1'b1;
    rd_en = 1'b1;
    @(negedge clk);
    wr_en = 1'b0;
    rd_en = 1'b0;
    #1;
    if (dout !== 8'd21 || empty !== 1'b0 || full !== 1'b0) begin
      $display("TEST_FAIL simultaneous push-pop changed occupancy");
      $finish;
    end
    read_expect(8'd22);
    if (empty !== 1'b1) begin
      $display("TEST_FAIL simultaneous push-pop left wrong count");
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
