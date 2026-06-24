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

  // Clock generation
  always #5 clk = ~clk;

  initial begin
    clk = 0;
    rst_n = 0;
    event_valid = 0;
    #10 rst_n = 1;
    #5;
    // Test sequence: send 5 events
    repeat (5) begin
      @(posedge clk) event_valid = 1;
      @(posedge clk) event_valid = 0;
      #10;
    end
    #20;
    // Check count
    if (count == 8'd5) begin
      $display("TEST_PASS");
    end else begin
      $display("TEST_FAIL");
    end
    #10 $finish;
  end

endmodule
