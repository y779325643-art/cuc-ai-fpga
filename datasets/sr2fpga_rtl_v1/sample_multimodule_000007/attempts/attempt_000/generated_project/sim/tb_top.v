`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg sample_valid;
  reg [7:0] sample;
  wire result_valid;
  wire [10:0] result;

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
    input [7:0] value;
    input [10:0] expected;
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
    sample = 8'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    send_and_expect(8'd1, 11'd1);
    send_and_expect(8'd2, 11'd4);
    send_and_expect(8'd3, 11'd8);

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
