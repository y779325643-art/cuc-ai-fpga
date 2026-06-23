`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg sample_valid;
  reg [11:0] sample;
  wire result_valid;
  wire [14:0] result;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(sample_valid),
    .sample(sample),
    .result_valid(result_valid),
    .result(result)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_and_expect;
    input [11:0] value;
    input [14:0] expected;
    begin
      @(negedge clk);
      sample = value;
      sample_valid = 1'b1;
      @(posedge clk);
      #1;
      if (result_valid !== 1'b1) begin
        $display("TEST_FAIL result_valid was not asserted");
        $finish;
      end
      if (result !== expected) begin
        $display("TEST_FAIL expected result=%0d got %0d", expected, result);
        $finish;
      end
      @(negedge clk);
      sample_valid = 1'b0;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    sample_valid = 1'b0;
    sample = 12'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    send_and_expect(12'd1, 15'd1);
    send_and_expect(12'd2, 15'd4);
    send_and_expect(12'd3, 15'd8);

    @(posedge clk);
    #1;
    if (result_valid !== 1'b0) begin
      $display("TEST_FAIL result_valid did not clear");
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endmodule
