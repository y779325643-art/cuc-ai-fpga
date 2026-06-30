`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  reg [7:0] in_data;
  wire in_ready;
  wire [7:0] sum;

  top uut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .in_ready(in_ready),
    .sum(sum)
  );

  // Clock generation: 100 MHz, 10 ns period
  initial clk = 0;
  always #5 clk = ~clk;

  // Golden model
  reg [7:0] pipe0_data;
  reg [7:0] pipe1_data;
  reg pipe0_valid;
  reg pipe1_valid;
  reg [7:0] expected_sum;
  integer check_fail;

  always @(posedge clk) begin
    if (!rst_n) begin
      pipe0_data <= 0;
      pipe1_data <= 0;
      pipe0_valid <= 0;
      pipe1_valid <= 0;
      expected_sum <= 0;
    end else begin
      // Shift pipeline: pipe1 <- pipe0, pipe0 <- new input if accepted
      pipe1_data <= pipe0_data;
      pipe1_valid <= pipe0_valid;
      pipe0_data <= 0;
      pipe0_valid <= 0;
      if (in_valid && in_ready) begin
        pipe0_data <= in_data;
        pipe0_valid <= 1;
      end
      // Accumulate when data reaches pipe1
      if (pipe1_valid) begin
        expected_sum <= expected_sum + pipe1_data;
      end
    end
  end

  // Continuous check on sum (using negedge to allow registers to settle)
  initial check_fail = 0;
  always @(negedge clk) begin
    if (rst_n && $time > 0) begin
      if (sum !== expected_sum) begin
        $display("TEST_FAIL: sum mismatch at time %t: sum = %d, expected = %d", $time, sum, expected_sum);
        check_fail = 1;
      end
    end
  end

  // Stimulus
  task send_sample(input [7:0] data);
    reg [31:0] timeout;
    begin
      timeout = 0;
      @(negedge clk);
      in_valid = 1'b1;
      in_data = data;
      while (!in_ready) begin
        @(posedge clk);
        timeout = timeout + 1;
        if (timeout > 1000) begin
          $display("TEST_FAIL: timeout waiting for in_ready");
          check_fail = 1;
          @(negedge clk)
          in_valid = 1'b0;
          disable send_sample;
        end
      end
      @(negedge clk);
      in_valid = 1'b0;
    end
  endtask

  initial begin
    // Initial conditions
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_data = 8'd0;

    // Hold reset for 5 cycles
    repeat (5) @(posedge clk);
    rst_n = 1'b1;
    @(posedge clk);

    // Test sequence: back-to-back transfers
    send_sample(8'd10);
    send_sample(8'd20);
    send_sample(8'd30);
    send_sample(8'd40);
    send_sample(8'd50);

    // Wait for pipeline to drain and final sum to settle
    repeat (5) @(posedge clk);

    if (check_fail) begin
      $display("TEST_FAIL");
    end else begin
      $display("TEST_PASS");
    end
    $finish;
  end

endmodule
