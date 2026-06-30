`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg feature_valid;
  wire feature_ready;
  reg [7:0] feature_data;
  reg weight_valid;
  wire weight_ready;
  reg [7:0] weight_data;
  reg [15:0] bias;
  wire score_valid;
  reg score_ready;
  wire [15:0] score_data;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .feature_valid(feature_valid),
    .feature_ready(feature_ready),
    .feature_data(feature_data),
    .weight_valid(weight_valid),
    .weight_ready(weight_ready),
    .weight_data(weight_data),
    .bias(bias),
    .score_valid(score_valid),
    .score_ready(score_ready),
    .score_data(score_data)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_pair;
    input [7:0] feature;
    input [7:0] weight;
    begin
      @(negedge clk);
      feature_valid = 1'b1;
      weight_valid = 1'b1;
      feature_data = feature;
      weight_data = weight;
      while (!(feature_ready && weight_ready)) begin
        @(negedge clk);
      end
      @(negedge clk);
      feature_valid = 1'b0;
      weight_valid = 1'b0;
      feature_data = 8'd0;
      weight_data = 8'd0;
    end
  endtask

  task expect_score;
    input [15:0] expected;
    begin
      wait_cycles = 0;
      while (score_valid !== 1'b1 && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (score_valid !== 1'b1) begin
        $display("TEST_FAIL score did not become valid");
        $finish;
      end
      if (score_data !== expected) begin
        $display("TEST_FAIL expected score=%0d got %0d", expected, score_data);
        $finish;
      end
      @(negedge clk);
    end
  endtask

  initial begin
    rst_n = 1'b0;
    feature_valid = 1'b0;
    feature_data = 8'd0;
    weight_valid = 1'b0;
    weight_data = 8'd0;
    bias = 16'd0;
    score_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    bias = 16'd3;
    send_pair(8'd1, 8'd2);
    send_pair(8'd2, 8'd3);
    send_pair(8'd3, 8'd4);
    send_pair(8'd4, 8'd5);
    expect_score(16'd43);

    bias = 16'd1;
    send_pair(8'd2, 8'd1);
    send_pair(8'd1, 8'd2);
    send_pair(8'd0, 8'd3);
    send_pair(8'd3, 8'd4);
    expect_score(16'd17);

    $display("TEST_PASS");
    $finish;
  end
endmodule
