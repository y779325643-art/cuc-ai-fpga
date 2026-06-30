`timescale 1ns / 1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in0_valid, in1_valid;
  reg [7:0] in0_data, in1_data;
  wire in0_ready, in1_ready;
  wire out_valid;
  wire [15:0] out_data;
  reg out_ready;

  top uut (.*);

  // Clock generation
  always #5 clk = ~clk;

  // Output ready toggling every cycle for backpressure exercise
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      out_ready <= 1'b0;
    else
      out_ready <= ~out_ready;
  end

  // Task to send a pair of inputs simultaneously
  task send_pair(input [7:0] data0, input [7:0] data1);
    begin
      @(negedge clk);
      in0_valid <= 1;
      in0_data <= data0;
      in1_valid <= 1;
      in1_data <= data1;
      @(negedge clk);
      while (!(in0_ready && in1_ready)) begin
        @(negedge clk);
      end
      @(negedge clk);
      in0_valid <= 0;
      in1_valid <= 0;
    end
  endtask

  // Task to check output data and handshake
  integer out_count = 0;
  task wait_check_output(input [15:0] expected);
    integer timeout = 1000000;
    begin
      // Wait for out_valid
      while (!out_valid && timeout > 0) begin
        @(negedge clk);
        timeout = timeout - 1;
      end
      if (timeout == 0) begin
        $display("TEST_FAIL: timeout waiting for out_valid");
        $finish;
      end
      if (out_data != expected) begin
        $display("TEST_FAIL: output data mismatch, expected %d, got %d", expected, out_data);
        $finish;
      end
      $display("Output %0d: got %d (expected %d)", out_count, out_data, expected);
      // Wait for handshake (out_valid goes low)
      while (out_valid && timeout > 0) begin
        @(negedge clk);
        timeout = timeout - 1;
      end
      if (timeout == 0) begin
        $display("TEST_FAIL: timeout waiting for output handshake");
        $finish;
      end
      out_count = out_count + 1;
    end
  endtask

  initial begin
    // Initialize
    clk = 0;
    rst_n = 0;
    in0_valid = 0;
    in1_valid = 0;
    in0_data = 0;
    in1_data = 0;
    out_count = 0;

    // Reset
    repeat(5) @(negedge clk);
    rst_n = 1;
    repeat(3) @(posedge clk);

    // Send first batch of 4 pairs
    send_pair(8'd0, 8'd1);
    send_pair(8'd0, 8'd2);
    send_pair(8'd0, 8'd3);
    send_pair(8'd0, 8'd4);

    // Send second batch of 4 pairs
    send_pair(8'd0, 8'd5);
    send_pair(8'd0, 8'd6);
    send_pair(8'd0, 8'd7);
    send_pair(8'd0, 8'd8);

    // Check outputs: first batch sum = 1+2+3+4 = 10, second batch sum = 5+6+7+8 = 26
    wait_check_output(16'd10);
    wait_check_output(16'd26);

    // All done
    $display("TEST_PASS");
    $finish;
  end

  // Timeout fail-safe
  initial begin
    #1000000;
    $display("TEST_FAIL: global timeout");
    $finish;
  end

endmodule
