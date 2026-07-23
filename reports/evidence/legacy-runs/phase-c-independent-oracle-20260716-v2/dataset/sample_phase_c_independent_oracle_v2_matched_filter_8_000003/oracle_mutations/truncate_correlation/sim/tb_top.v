`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg signed [7:0] in_sample;
  wire out_valid;
  reg out_ready;
  wire signed [17:0] correlation;
  reg signed [17:0] held_correlation;
  localparam INPUT_RECORD_WIDTH = 11;
  localparam EXPECTED_RECORD_WIDTH = 18;
  localparam MAX_ORACLE_TRANSACTIONS = 4096;
  reg [INPUT_RECORD_WIDTH-1:0] oracle_inputs [0:MAX_ORACLE_TRANSACTIONS-1];
  reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected [0:MAX_ORACLE_TRANSACTIONS-1];
  reg [INPUT_RECORD_WIDTH-1:0] oracle_input_record;
  reg signed [EXPECTED_RECORD_WIDTH-1:0] oracle_expected_correlation;
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
    .out_valid(out_valid),
    .out_ready(out_ready),
    .correlation(correlation)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_and_expect;
    input signed [7:0] value;
    input signed [17:0] expected;
    begin
      @(negedge clk);
      while (in_ready !== 1'b1) begin
        @(negedge clk);
      end
      in_sample = value;
      in_valid = 1'b1;
      @(posedge clk);
      #1;
      if (out_valid !== 1'b1 || correlation !== expected) begin
        $display("TEST_FAIL correlation expected=%0d actual=%0d", expected, correlation);
        $finish;
      end
      @(negedge clk);
      in_valid = 1'b0;
    end
  endtask

  task oracle_reset_dut;
    begin
      @(negedge clk);
      rst_n = 1'b0;
      in_valid = 1'b0;
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
    out_ready = 1'b1;
    held_correlation = 18'sd0;
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
        oracle_expected_correlation = oracle_expected[oracle_item_index];
        oracle_stall_cycles = oracle_input_record[10:9];
        if (oracle_input_record[8]) begin
          oracle_reset_dut;
        end
        @(negedge clk);
        while (in_ready !== 1'b1) begin
          @(negedge clk);
        end
        out_ready = oracle_stall_cycles == 0;
        in_sample = oracle_input_record[7:0];
        in_valid = 1'b1;
        @(posedge clk);
        #1;
        if (out_valid !== 1'b1 || correlation !== oracle_expected_correlation) begin
          $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"correlation\":\"0x%0h\"},\"actual\":{\"correlation\":\"0x%0h\",\"out_valid\":\"%0b\"}}",
                   oracle_scenario_id, oracle_scenario_class, oracle_item_index, oracle_expected_correlation, correlation, out_valid);
          $display("TEST_FAIL functional mismatch");
          $finish;
        end
        held_correlation = correlation;
        @(negedge clk);
        in_valid = 1'b0;
        if (oracle_stall_cycles > 0) begin
          in_sample = ~oracle_input_record[7:0];
          in_valid = 1'b1;
          #1;
          if (in_ready !== 1'b0) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"in_ready\":0},\"actual\":{\"in_ready\":\"%0b\"}}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index, in_ready);
            $display("TEST_FAIL accepted sample while output stalled");
            $finish;
          end
        end
        for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
          @(posedge clk);
          #1;
          if (out_valid !== 1'b1 || correlation !== held_correlation || in_ready !== 1'b0) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"correlation\":\"0x%0h\",\"out_valid\":1,\"in_ready\":0},\"actual\":{\"correlation\":\"0x%0h\",\"out_valid\":\"%0b\",\"in_ready\":\"%0b\"}}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index, held_correlation, correlation, out_valid, in_ready);
            $display("TEST_FAIL correlation changed under backpressure");
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
      $display("TEST_PASS");
      $finish;
    end else begin
      repeat (2) @(posedge clk);
      rst_n = 1'b1;

    // Template [-1, 2, -3, 4] responds to this reversed known pulse with 30.
    send_and_expect(8'sd4, -18'sd4);
    send_and_expect(-8'sd3, 18'sd11);
    send_and_expect(8'sd2, -18'sd20);
    send_and_expect(-8'sd1, 18'sd30);
    send_and_expect(8'sd127, -18'sd147);

    @(negedge clk);
    while (in_ready !== 1'b1) begin
      @(negedge clk);
    end
    out_ready = 1'b0;
    in_sample = -8'sd8;
    in_valid = 1'b1;
    @(posedge clk);
    #1;
    if (out_valid !== 1'b1 || correlation !== 18'sd273) begin
      $display("TEST_FAIL failed to capture stalled correlation");
      $finish;
    end
    held_correlation = correlation;
    @(negedge clk);
    in_valid = 1'b0;
    repeat (2) begin
      @(posedge clk);
      #1;
      if (out_valid !== 1'b1 || correlation !== held_correlation) begin
        $display("TEST_FAIL correlation changed under backpressure");
        $finish;
      end
    end
    @(negedge clk);
    out_ready = 1'b1;
    @(posedge clk);

    @(negedge clk);
    rst_n = 1'b0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    send_and_expect(-8'sd4, 18'sd4);

    $display("TEST_PASS");
    $finish;
    end
  end

  initial begin
    #8000;
    $display("TEST_FAIL timeout");
    $finish;
  end
endmodule
