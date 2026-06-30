`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [7:0] in_data;
  wire out0_valid;
  reg out0_ready;
  wire [7:0] out0_data;
  wire out1_valid;
  reg out1_ready;
  wire [7:0] out1_data;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out0_valid(out0_valid),
    .out0_ready(out0_ready),
    .out0_data(out0_data),
    .out1_valid(out1_valid),
    .out1_ready(out1_ready),
    .out1_data(out1_data)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_data = 8'd0;
    out0_ready = 1'b1;
    out1_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    in_valid = 1'b1;
    in_data = 8'd165;
    @(negedge clk);
    in_valid = 1'b0;
    in_data = 8'd0;
    repeat (3) @(posedge clk);
    #1;

    if (out0_valid !== 1'b1 || out1_valid !== 1'b1) begin
      $display("TEST_FAIL fork outputs not valid");
      $finish;
    end
    if (out0_data !== 8'd165 || out1_data !== 8'd165) begin
      $display("TEST_FAIL fork data mismatch out0=%0d out1=%0d", out0_data, out1_data);
      $finish;
    end
    if (in_ready !== 1'b1) begin
      $display("TEST_FAIL fork input not ready");
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endmodule
