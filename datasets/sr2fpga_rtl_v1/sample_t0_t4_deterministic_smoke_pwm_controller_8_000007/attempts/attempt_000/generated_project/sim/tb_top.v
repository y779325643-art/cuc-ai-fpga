`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg [7:0] duty;
  wire pwm_out;
  integer high_count;
  integer i;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .duty(duty),
    .pwm_out(pwm_out)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    duty = 8'd3;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;

    high_count = 0;
    #1;
    if (pwm_out === 1'b1) begin
      high_count = high_count + 1;
    end
    for (i = 1; i < 8; i = i + 1) begin
      @(posedge clk);
      #1;
      if (pwm_out === 1'b1) begin
        high_count = high_count + 1;
      end
    end

    if (high_count != 3) begin
      $display("TEST_FAIL expected %0d high cycles got %0d", 3, high_count);
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
