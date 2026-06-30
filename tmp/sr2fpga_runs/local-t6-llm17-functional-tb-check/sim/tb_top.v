`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg signed [7:0] reward;
  reg signed [7:0] value;
  reg signed [7:0] next_value;
  reg [7:0] gamma;
  reg [7:0] alpha;
  wire out_valid;
  reg out_ready;
  wire signed [7:0] td_error;
  wire signed [7:0] updated_value;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .reward(reward),
    .value(value),
    .next_value(next_value),
    .gamma(gamma),
    .alpha(alpha),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .td_error(td_error),
    .updated_value(updated_value)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_update;
    input signed [7:0] reward_i;
    input signed [7:0] value_i;
    input signed [7:0] next_value_i;
    input [7:0] gamma_i;
    input [7:0] alpha_i;
    begin
      @(negedge clk);
      in_valid = 1'b1;
      reward = reward_i;
      value = value_i;
      next_value = next_value_i;
      gamma = gamma_i;
      alpha = alpha_i;
      while (!in_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      in_valid = 1'b0;
    end
  endtask

  task expect_update;
    input signed [7:0] expected_error;
    input signed [7:0] expected_value;
    begin
      wait_cycles = 0;
      while (out_valid !== 1'b1 && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (out_valid !== 1'b1) begin
        $display("TEST_FAIL output did not become valid");
        $finish;
      end
      if (td_error !== expected_error || updated_value !== expected_value) begin
        $display(
          "TEST_FAIL expected td=%0d value=%0d got td=%0d value=%0d",
          expected_error,
          expected_value,
          td_error,
          updated_value
        );
        $finish;
      end
      @(negedge clk);
    end
  endtask

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    reward = 8'sd0;
    value = 8'sd0;
    next_value = 8'sd0;
    gamma = 8'd0;
    alpha = 8'd0;
    out_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    send_update(8'sd4, 8'sd10, 8'sd20, 8'd8, 8'd4);
    expect_update(8'sd4, 8'sd11);

    send_update(8'sd2, 8'sd6, 8'sd16, 8'd8, 8'd8);
    expect_update(8'sd4, 8'sd8);

    $display("TEST_PASS");
    $finish;
  end
endmodule
