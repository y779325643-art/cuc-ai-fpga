`timescale 1ns/1ps
module tb_top;

  reg         clk;
  reg         rst_n;
  reg         in0_valid;
  reg  [7:0]  in0_data;
  wire        in0_ready;
  reg         in1_valid;
  reg  [7:0]  in1_data;
  wire        in1_ready;
  wire        out_valid;
  wire [7:0]  out_data;

  // input sequences
  reg [7:0] seq_in0 [0:4];
  reg [7:0] seq_in1 [0:4];
  reg [7:0] expected_out [0:4];
  integer    input_cnt;
  integer    output_cnt;
  integer    timeout;
  reg        fail;

  // instantiate DUT
  top dut (
    .clk       (clk),
    .rst_n     (rst_n),
    .in0_valid (in0_valid),
    .in0_data  (in0_data),
    .in0_ready (in0_ready),
    .in1_valid (in1_valid),
    .in1_data  (in1_data),
    .in1_ready (in1_ready),
    .out_valid (out_valid),
    .out_data  (out_data)
  );

  // clock generation (100 MHz -> 10 ns period)
  initial clk = 0;
  always #5 clk = ~clk;

  // task to send both inputs in lockstep
  task send_both(input [7:0] d0, input [7:0] d1);
    begin
      @(negedge clk);
      in0_valid <= 1'b1;
      in0_data  <= d0;
      in1_valid <= 1'b1;
      in1_data  <= d1;
      // wait until handshake completes (both readys high at negedge)
      timeout = 0;
      do begin
        @(negedge clk);
        timeout = timeout + 1;
        if (timeout > 1000) begin
          $display("TEST_FAIL: timeout waiting for in ready");
          fail = 1;
          disable send_both;
        end
      end while (!(in0_ready && in1_ready));
      in0_valid <= 1'b0;
      in1_valid <= 1'b0;
    end
  endtask

  initial begin
    // initialize sequences (workaround for aggregate init)
    seq_in0[0] = 8'd1;  seq_in1[0] = 8'd10;
    seq_in0[1] = 8'd2;  seq_in1[1] = 8'd20;
    seq_in0[2] = 8'd3;  seq_in1[2] = 8'd30;
    seq_in0[3] = 8'd4;  seq_in1[3] = 8'd40;
    seq_in0[4] = 8'd5;  seq_in1[4] = 8'd50;

    // expected outputs: cumulative sum of (seq_in0[i]+seq_in1[i])
    // pair sums: 11, 22, 33, 44, 55 -> cumulative: 11, 33, 66, 110, 165
    expected_out[0] = 8'd11;
    expected_out[1] = 8'd33;
    expected_out[2] = 8'd66;
    expected_out[3] = 8'd110;
    expected_out[4] = 8'd165;

    fail = 0;
    input_cnt = 0;
    output_cnt = 0;

    // initial values
    in0_valid = 0;
    in0_data  = 0;
    in1_valid = 0;
    in1_data  = 0;
    rst_n = 1;

    // reset sequence
    @(negedge clk); rst_n = 0;
    @(negedge clk); rst_n = 1;
    @(negedge clk); // extra cycles
    @(negedge clk);

    // send all input pairs
    for (input_cnt = 0; input_cnt < 5; input_cnt = input_cnt + 1) begin
      send_both(seq_in0[input_cnt], seq_in1[input_cnt]);
    end

    // wait for 5 output transactions
    for (output_cnt = 0; output_cnt < 5; output_cnt = output_cnt + 1) begin
      timeout = 0;
      // wait for out_valid high
      while (!out_valid) begin
        @(negedge clk);
        timeout = timeout + 1;
        if (timeout > 1000) begin
          $display("TEST_FAIL: timeout waiting for out_valid (output_cnt=%0d)", output_cnt);
          fail = 1;
          disable output_wait;
        end
      end
      // out_valid is high this cycle, check data on negedge to allow settling
      @(negedge clk); // wait half cycle
      if (out_data !== expected_out[output_cnt]) begin
        $display("TEST_FAIL: mismatch at output_cnt=%0d: got %0d, expected %0d",
                 output_cnt, out_data, expected_out[output_cnt]);
        fail = 1;
      end
    end

    if (!fail) begin
      $display("TEST_PASS");
    end
    $finish;
  end

endmodule
