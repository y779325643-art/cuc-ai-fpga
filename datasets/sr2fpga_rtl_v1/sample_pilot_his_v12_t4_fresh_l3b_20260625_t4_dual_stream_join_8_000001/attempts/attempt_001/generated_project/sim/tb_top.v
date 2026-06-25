`timescale 1ns / 1ps

module tb_top;

  parameter DATA_WIDTH = 8;
  reg clk;
  reg rst_n;
  reg [DATA_WIDTH-1:0] in0_data, in1_data;
  reg in0_valid, in1_valid, out_ready;
  wire in0_ready, in1_ready, out_valid;
  wire [DATA_WIDTH-1:0] out_data;

  top #(
    .DATA_WIDTH(DATA_WIDTH)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_ready(in0_ready),
    .in0_data(in0_data),
    .in1_valid(in1_valid),
    .in1_ready(in1_ready),
    .in1_data(in1_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
  );

  // Clock generation
  always #5 clk = ~clk;

  initial begin
    clk = 0;
    rst_n = 0;
    in0_valid = 0;
    in1_valid = 0;
    out_ready = 0;
    in0_data = 0;
    in1_data = 0;
    #22 rst_n = 1;
    #10;

    // Test scenario: basic join and accumulate
    // Stimulus sequences
    reg [7:0] seq0 [0:3];
    reg [7:0] seq1 [0:3];
    integer i;
    reg fail;
    fail = 0;

    seq0[0] = 8'd10;
    seq0[1] = 8'd20;
    seq0[2] = 8'd30;
    seq0[3] = 8'd40;
    seq1[0] = 8'd1;
    seq1[1] = 8'd2;
    seq1[2] = 8'd3;
    seq1[3] = 8'd4;

    // Expected accumulated sums
    reg [7:0] expected [0:3];
    expected[0] = 8'd11;
    expected[1] = 8'd33;  // 11+22
    expected[2] = 8'd66;  // 33+33
    expected[3] = 8'd110; // 66+44

    out_ready = 1;

    // Reset and do a clean test
    #100;
    @(posedge clk);
    rst_n = 0;
    @(posedge clk);
    rst_n = 1;

    // Wait 2 cycles
    repeat(2) @(posedge clk);

    // Drive inputs for 4 cycles with backpressure
    for (i=0; i<4; i=i+1) begin
      @(posedge clk);
      in0_valid <= 1;
      in1_valid <= 1;
      in0_data <= seq0[i];
      in1_data <= seq1[i];
    end
    @(posedge clk);
    in0_valid <= 0;
    in1_valid <= 0;

    // Wait for all outputs to appear: expect 4 output values
    reg [7:0] out_samples [0:3];
    integer sample_idx;
    sample_idx = 0;
    integer timeout;
    timeout = 0;

    while (sample_idx < 4 && timeout < 50) begin
      @(posedge clk);
      timeout = timeout + 1;
      if (out_valid && out_ready) begin
        out_samples[sample_idx] = out_data;
        sample_idx = sample_idx + 1;
      end
    end

    if (timeout >= 50) begin
      $display("TEST_FAIL: Timeout waiting for outputs");
      fail = 1;
    end else begin
      for (i=0; i<4; i=i+1) begin
        if (out_samples[i] !== expected[i]) begin
          $display("TEST_FAIL: Mismatch at index %0d: expected %0d, got %0d", i, expected[i], out_samples[i]);
          fail = 1;
        end
      end
    end

    // Additional test: reset behavior
    @(posedge clk);
    rst_n = 0;
    @(posedge clk);
    rst_n = 1;
    // After reset, accumulator should be 0
    @(posedge clk);
    if (out_valid) begin
      if (out_data !== 0) begin
        $display("TEST_FAIL: After reset, output not zero");
        fail = 1;
      end
    end

    if (!fail) begin
      $display("TEST_PASS");
    end
    $finish;
  end

endmodule
