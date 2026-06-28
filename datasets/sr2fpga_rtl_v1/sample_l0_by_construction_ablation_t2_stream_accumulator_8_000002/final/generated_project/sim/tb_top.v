`timescale 1ns/1ps

module tb_top;

  reg clk;
  reg rst_n;
  reg [7:0] in_data;
  reg in_valid;
  wire in_ready;
  wire [7:0] sum;

  top uut (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in_data),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .sum(sum)
  );

  always #5 clk = ~clk;

  reg [7:0] test_data [0:3];
  reg [7:0] expected_sum [0:3];
  integer i;

  initial begin
    clk = 0;
    rst_n = 0;
    in_valid = 0;
    in_data = 0;

    test_data[0] = 8'd5;
    test_data[1] = 8'd10;
    test_data[2] = 8'd20;
    test_data[3] = 8'd35;

    expected_sum[0] = 8'd5;
    expected_sum[1] = 8'd15;
    expected_sum[2] = 8'd35;
    expected_sum[3] = 8'd70;

    @(negedge clk);
    rst_n = 1;

    repeat (3) @(posedge clk);

    if (sum !== 8'd0) begin
      $display("TEST_FAIL");
      $finish;
    end

    for (i = 0; i < 4; i = i + 1) begin
      integer timeout;
      timeout = 0;
      while (!in_ready) begin
        @(posedge clk);
        timeout = timeout + 1;
        if (timeout > 1000) begin
          $display("TEST_FAIL: Timeout waiting for in_ready");
          $finish;
        end
      end

      @(negedge clk);
      in_data = test_data[i];
      in_valid = 1'b1;

      @(posedge clk);

      @(negedge clk);
      in_valid = 1'b0;

      if (sum !== expected_sum[i]) begin
        $display("TEST_FAIL: Mismatch at i=%d, sum=%d, expected=%d", i, sum, expected_sum[i]);
        $finish;
      end
    end

    $display("TEST_PASS");
    $finish;
  end

endmodule
