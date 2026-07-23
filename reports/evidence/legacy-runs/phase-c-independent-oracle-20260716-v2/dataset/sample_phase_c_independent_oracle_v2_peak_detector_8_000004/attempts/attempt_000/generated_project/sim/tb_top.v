`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg signed [7:0] in_sample;
  reg in_last;
  wire out_valid;
  reg out_ready;
  wire peak_found;
  wire signed [7:0] peak_value;
  wire [7:0] peak_index;
  reg held_found;
  reg signed [7:0] held_value;
  reg [7:0] held_index;
  localparam INPUT_RECORD_WIDTH = 12;
  localparam EXPECTED_RECORD_WIDTH = 18;
  localparam MAX_ORACLE_TRANSACTIONS = 4096;
  reg [INPUT_RECORD_WIDTH-1:0] oracle_inputs [0:MAX_ORACLE_TRANSACTIONS-1];
  reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected [0:MAX_ORACLE_TRANSACTIONS-1];
  reg [INPUT_RECORD_WIDTH-1:0] oracle_input_record;
  reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected_record;
  reg oracle_expected_found;
  reg signed [7:0] oracle_expected_value;
  reg [7:0] oracle_expected_index;
  string oracle_input_path;
  string oracle_expected_path;
  string oracle_scenario_id;
  string oracle_scenario_class;
  integer oracle_enabled;
  integer oracle_transaction_count;
  integer oracle_item_index;
  integer oracle_stall_index;
  integer oracle_stall_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_sample(in_sample),
    .in_last(in_last),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .peak_found(peak_found),
    .peak_value(peak_value),
    .peak_index(peak_index)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_sample;
    input signed [7:0] value;
    input last;
    begin
      @(negedge clk);
      while (in_ready !== 1'b1) begin
        @(negedge clk);
      end
      in_sample = value;
      in_last = last;
      in_valid = 1'b1;
      @(posedge clk);
      #1;
      @(negedge clk);
      in_valid = 1'b0;
      in_last = 1'b0;
    end
  endtask

  task expect_result;
    input expected_found;
    input signed [7:0] expected_value;
    input [7:0] expected_index;
    begin
      while (out_valid !== 1'b1) begin
        @(posedge clk);
        #1;
      end
      if (peak_found !== expected_found || peak_value !== expected_value || peak_index !== expected_index) begin
        $display("TEST_FAIL result expected found=%0d value=%0d index=%0d actual found=%0d value=%0d index=%0d", expected_found, expected_value, expected_index, peak_found, peak_value, peak_index);
        $finish;
      end
      @(posedge clk);
      #1;
    end
  endtask

  task oracle_reset_dut;
    begin
      @(negedge clk);
      rst_n = 1'b0;
      in_valid = 1'b0;
      in_last = 1'b0;
      out_ready = 1'b1;
      repeat (2) @(posedge clk);
      @(negedge clk);
      rst_n = 1'b1;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_sample = 8'sd0;
    in_last = 1'b0;
    out_ready = 1'b1;
    held_found = 1'b0;
    held_value = 8'sd0;
    held_index = 8'd0;
    oracle_transaction_count = 0;
    oracle_enabled = $value$plusargs("ORACLE_INPUT=%s", oracle_input_path);
    if (oracle_enabled) begin
      if (!$value$plusargs("ORACLE_EXPECTED=%s", oracle_expected_path) ||
          !$value$plusargs("ORACLE_SCENARIO_ID=%s", oracle_scenario_id) ||
          !$value$plusargs("ORACLE_SCENARIO_CLASS=%s", oracle_scenario_class) ||
          !$value$plusargs("ORACLE_TRANSACTION_COUNT=%d", oracle_transaction_count)) begin
        $display("TEST_FAIL missing oracle plusargs");
        $finish;
      end
      if (oracle_transaction_count <= 0 || oracle_transaction_count > MAX_ORACLE_TRANSACTIONS) begin
        $display("TEST_FAIL invalid oracle transaction count");
        $finish;
      end
      $readmemh(oracle_input_path, oracle_inputs, 0, oracle_transaction_count - 1);
      $readmemh(oracle_expected_path, oracle_expected, 0, oracle_transaction_count - 1);
      repeat (2) @(posedge clk);
      rst_n = 1'b1;
      for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count; oracle_item_index = oracle_item_index + 1) begin
        oracle_input_record = oracle_inputs[oracle_item_index];
        oracle_expected_record = oracle_expected[oracle_item_index];
        oracle_expected_value = oracle_expected_record[7:0];
        oracle_expected_index = oracle_expected_record[15:8];
        oracle_expected_found = oracle_expected_record[16];
        oracle_stall_cycles = oracle_input_record[11:10];
        if (oracle_input_record[9]) begin
          oracle_reset_dut;
        end
        @(negedge clk);
        while (in_ready !== 1'b1) begin
          @(negedge clk);
        end
        out_ready = oracle_stall_cycles == 0;
        in_sample = oracle_input_record[7:0];
        in_last = oracle_input_record[8];
        in_valid = 1'b1;
        @(posedge clk);
        #1;
        if (oracle_expected_record[17]) begin
          if (out_valid !== 1'b1 || peak_found !== oracle_expected_found ||
              peak_value !== oracle_expected_value || peak_index !== oracle_expected_index) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"found\":%0d,\"value\":\"0x%0h\",\"index\":%0d},\"actual\":{\"found\":\"%0b\",\"value\":\"0x%0h\",\"index\":\"0x%0h\",\"out_valid\":\"%0b\"}}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                     oracle_expected_found, oracle_expected_value, oracle_expected_index,
                     peak_found, peak_value, peak_index, out_valid);
            $display("TEST_FAIL functional mismatch");
            $finish;
          end
          held_found = peak_found;
          held_value = peak_value;
          held_index = peak_index;
        end else if (out_valid !== 1'b0) begin
          $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"out_valid\":0},\"actual\":{\"out_valid\":\"%0b\"}}",
                   oracle_scenario_id, oracle_scenario_class, oracle_item_index, out_valid);
          $display("TEST_FAIL unexpected output");
          $finish;
        end
        @(negedge clk);
        in_valid = 1'b0;
        in_last = 1'b0;
        if (oracle_expected_record[17]) begin
          if (oracle_stall_cycles > 0) begin
            in_sample = ~oracle_input_record[7:0];
            in_valid = 1'b1;
            #1;
            if (in_ready !== 1'b0) begin
              $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"in_ready\":0},\"actual\":{\"in_ready\":\"%0b\"}}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index, in_ready);
              $display("TEST_FAIL accepted sample while result stalled");
              $finish;
            end
          end
          for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
            @(posedge clk);
            #1;
            if (out_valid !== 1'b1 || peak_found !== held_found || peak_value !== held_value ||
                peak_index !== held_index || in_ready !== 1'b0) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"found\":%0d,\"value\":\"0x%0h\",\"index\":%0d,\"in_ready\":0},\"actual\":{\"found\":\"%0b\",\"value\":\"0x%0h\",\"index\":\"0x%0h\",\"in_ready\":\"%0b\"}}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                       held_found, held_value, held_index, peak_found, peak_value, peak_index, in_ready);
              $display("TEST_FAIL result changed under backpressure");
              $finish;
            end
          end
          @(negedge clk);
          in_valid = 1'b0;
          out_ready = 1'b1;
          @(posedge clk);
          #1;
          if (out_valid !== 1'b0) begin
            $display("TEST_FAIL out_valid did not clear");
            $finish;
          end
        end
      end
      $display("TEST_PASS");
      $finish;
    end else begin
      repeat (2) @(posedge clk);
      rst_n = 1'b1;

    // A frame without a threshold-qualified sample produces the defined empty result.
    send_sample(-8'sd3, 1'b0);
    send_sample(8'sd0, 1'b0);
    send_sample(8'sd9, 1'b1);
    expect_result(1'b0, 8'sd0, 8'd0);

    // Equality at THRESHOLD qualifies, and a later larger sample wins.
    send_sample(8'sd10, 1'b0);
    send_sample(8'sd12, 1'b0);
    send_sample(8'sd15, 1'b0);
    send_sample(8'sd13, 1'b1);
    expect_result(1'b1, 8'sd15, 8'd2);

    // Equal maxima retain the first accepted index.
    send_sample(8'sd11, 1'b0);
    send_sample(8'sd16, 1'b0);
    send_sample(8'sd16, 1'b0);
    send_sample(8'sd14, 1'b1);
    expect_result(1'b1, 8'sd16, 8'd1);

    // The final accepted sample participates in the frame maximum.
    send_sample(8'sd11, 1'b0);
    send_sample(8'sd14, 1'b0);
    send_sample(8'sd19, 1'b1);
    expect_result(1'b1, 8'sd19, 8'd2);

    // A completed output remains unchanged while downstream is stalled.
    @(negedge clk);
    out_ready = 1'b0;
    send_sample(8'sd10, 1'b1);
    if (out_valid !== 1'b1 || peak_found !== 1'b1 || peak_value !== 8'sd10 || peak_index !== 8'd0) begin
      $display("TEST_FAIL stalled result was not captured");
      $finish;
    end
    held_found = peak_found;
    held_value = peak_value;
    held_index = peak_index;
    repeat (2) begin
      @(posedge clk);
      #1;
      if (out_valid !== 1'b1 || peak_found !== held_found || peak_value !== held_value || peak_index !== held_index) begin
        $display("TEST_FAIL result changed under backpressure");
        $finish;
      end
    end
    @(negedge clk);
    out_ready = 1'b1;
    @(posedge clk);

    // Reset discards partial-frame state and restarts indexing at zero.
    send_sample(8'sd20, 1'b0);
    @(negedge clk);
    rst_n = 1'b0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    send_sample(8'sd10, 1'b1);
    expect_result(1'b1, 8'sd10, 8'd0);

    $display("TEST_PASS");
    $finish;
    end
  end

  initial begin
    #2000;
    $display("TEST_FAIL timeout");
    $finish;
  end
endmodule
