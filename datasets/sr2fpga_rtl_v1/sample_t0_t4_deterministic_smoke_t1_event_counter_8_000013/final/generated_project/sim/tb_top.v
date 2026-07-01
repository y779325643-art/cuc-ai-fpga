`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg event_valid;
  wire [7:0] count;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .event_valid(event_valid),
    .count(count)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task pulse_event;
    begin
      @(negedge clk);
      event_valid = 1'b1;
      @(negedge clk);
      event_valid = 1'b0;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    event_valid = 1'b0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    pulse_event();
    pulse_event();
    repeat (2) @(posedge clk);
    #1;
    if (count !== 8'd2) begin
      $display("TEST_FAIL expected count=2 got %0d", count);
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
