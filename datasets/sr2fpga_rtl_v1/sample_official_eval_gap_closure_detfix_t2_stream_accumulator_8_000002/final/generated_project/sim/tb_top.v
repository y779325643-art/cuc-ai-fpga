`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [7:0] in_data;
  wire sample_valid;
  wire [11:0] sum;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .sample_valid(sample_valid),
    .sum(sum)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_sample;
    input [7:0] value;
    begin
      @(negedge clk);
      in_valid = 1'b1;
      in_data = value;
      @(negedge clk);
      in_valid = 1'b0;
      in_data = 8'd0;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_data = 8'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    send_sample(8'd3);
    send_sample(8'd4);
    repeat (2) @(posedge clk);
    #1;

    if (sum !== 12'd7) begin
      $display("TEST_FAIL expected sum=7 got %0d", sum);
      $finish;
    end
    if (in_ready !== 1'b1) begin
      $display("TEST_FAIL in_ready not asserted");
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endmodule
