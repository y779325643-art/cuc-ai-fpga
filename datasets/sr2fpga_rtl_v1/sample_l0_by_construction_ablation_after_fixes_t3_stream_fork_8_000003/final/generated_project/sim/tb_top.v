`timescale 1ns / 1ps
module tb_top;
  reg clk;
  reg reset_n;
  reg in_valid;
  reg [7:0] in_data;
  wire in_ready;
  wire out0_valid;
  wire [7:0] out0_data;
  reg out0_ready;
  wire out1_valid;
  wire [7:0] out1_data;
  reg out1_ready;

  top uut (
    .clk(clk),
    .reset_n(reset_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .in_ready(in_ready),
    .out0_valid(out0_valid),
    .out0_data(out0_data),
    .out0_ready(out0_ready),
    .out1_valid(out1_valid),
    .out1_data(out1_data),
    .out1_ready(out1_ready)
  );

  always #5 clk = ~clk;

  reg [7:0] expected_data [0:19];
  integer expected_count, out0_received, out1_received;
  integer timeout;

  task send_input;
    input [7:0] data;
    begin
      in_data = data;
      in_valid = 1;
      @(posedge clk);
      while (!in_ready) @(posedge clk);
      @(negedge clk);
      in_valid = 0;
    end
  endtask

  initial begin
    expected_data[0] = 8'd1;
    expected_data[1] = 8'd2;
    expected_data[2] = 8'd3;
    expected_data[3] = 8'd4;
    expected_data[4] = 8'd5;
    expected_data[5] = 8'd6;
    expected_data[6] = 8'd7;
    expected_data[7] = 8'd8;
    expected_data[8] = 8'd9;
    expected_data[9] = 8'd10;
    expected_data[10] = 8'd11;
    expected_data[11] = 8'd12;
    expected_data[12] = 8'd13;
    expected_data[13] = 8'd14;
    expected_data[14] = 8'd15;
    expected_data[15] = 8'd16;
    expected_data[16] = 8'd17;
    expected_data[17] = 8'd18;
    expected_data[18] = 8'd19;
    expected_data[19] = 8'd20;

    clk = 0;
    reset_n = 0;
    in_valid = 0;
    out0_ready = 0;
    out1_ready = 0;

    @(negedge clk);
    reset_n = 1;

    for (expected_count = 0; expected_count < 20; expected_count = expected_count + 1) begin
      send_input(expected_data[expected_count]);
    end

    out0_received = 0;
    out1_received = 0;
    timeout = 1000;
    while ((out0_received < 20 || out1_received < 20) && timeout > 0) begin
      @(negedge clk);
      if (out0_valid && out0_ready) begin
        if (out0_data !== expected_data[out0_received]) begin
          $display("TEST_FAIL: out0 mismatch at index %0d: expected %0d, got %0d", out0_received, expected_data[out0_received], out0_data);
          $finish;
        end
        out0_received = out0_received + 1;
      end
      if (out1_valid && out1_ready) begin
        if (out1_data !== expected_data[out1_received]) begin
          $display("TEST_FAIL: out1 mismatch at index %0d: expected %0d, got %0d", out1_received, expected_data[out1_received], out1_data);
          $finish;
        end
        out1_received = out1_received + 1;
      end
      timeout = timeout - 1;
    end

    if (timeout == 0) begin
      $display("TEST_FAIL: timeout waiting for outputs");
      $finish;
    end

    $display("TEST_PASS");
    $finish;
  end

  always @(negedge clk) begin
    out0_ready <= $random % 2;
    out1_ready <= $random % 2;
  end
endmodule
