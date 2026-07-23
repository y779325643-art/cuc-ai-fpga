`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg sample_valid;
  wire sample_ready;
  reg signed [7:0] sample;
  wire result_valid;
  reg result_ready;
  wire signed [11:0] result;
  localparam RESULT_WIDTH = 12;
  localparam INPUT_RECORD_WIDTH = 11;
  localparam EXPECTED_RECORD_WIDTH = 13;
  localparam MAX_ORACLE_TRANSACTIONS = 4096;
  reg [INPUT_RECORD_WIDTH-1:0] oracle_inputs [0:MAX_ORACLE_TRANSACTIONS-1];
  reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected [0:MAX_ORACLE_TRANSACTIONS-1];
  reg [INPUT_RECORD_WIDTH-1:0] oracle_input_record;
  reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected_record;
  reg signed [RESULT_WIDTH-1:0] oracle_expected_result;
  reg signed [RESULT_WIDTH-1:0] oracle_held_result;
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
    .sample_valid(sample_valid),
    .sample_ready(sample_ready),
    .sample(sample),
    .result_valid(result_valid),
    .result_ready(result_ready),
    .result(result)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_sample;
    input signed [7:0] value;
    begin
      @(negedge clk);
      while (sample_ready !== 1'b1) begin
        @(negedge clk);
      end
      sample = value;
      sample_valid = 1'b1;
      @(posedge clk);
      #1;
      @(negedge clk);
      sample_valid = 1'b0;
    end
  endtask

  task send_vector_and_expect;
    input signed [7:0] value0;
    input signed [7:0] value1;
    input signed [7:0] value2;
    input signed [7:0] value3;
    input signed [11:0] expected;
    begin
      send_sample(value0);
      send_sample(value1);
      send_sample(value2);
      send_sample(value3);
      if (result_valid !== 1'b1 || result !== expected) begin
        $display("TEST_FAIL expected result=%0d got valid=%0b result=%0d", expected, result_valid, result);
        $finish;
      end
    end
  endtask

  task oracle_reset_dut;
    begin
      @(negedge clk);
      rst_n = 1'b0;
      sample_valid = 1'b0;
      result_ready = 1'b1;
      repeat (2) @(posedge clk);
      @(negedge clk);
      rst_n = 1'b1;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    sample_valid = 1'b0;
    sample = 8'sd0;
    result_ready = 1'b1;
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
      $readmemh(oracle_input_path, oracle_inputs);
      $readmemh(oracle_expected_path, oracle_expected);
      repeat (2) @(posedge clk);
      rst_n = 1'b1;
      for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count; oracle_item_index = oracle_item_index + 1) begin
        oracle_input_record = oracle_inputs[oracle_item_index];
        oracle_expected_record = oracle_expected[oracle_item_index];
        oracle_expected_result = oracle_expected_record[RESULT_WIDTH-1:0];
        oracle_stall_cycles = oracle_input_record[10:9];
        if (oracle_input_record[8]) begin
          oracle_reset_dut;
        end
        @(negedge clk);
        while (sample_ready !== 1'b1) begin
          @(negedge clk);
        end
        result_ready = oracle_stall_cycles == 0;
        sample = oracle_input_record[7:0];
        sample_valid = 1'b1;
        @(posedge clk);
        #1;
        if (oracle_expected_record[RESULT_WIDTH]) begin
          if (result_valid !== 1'b1 || result !== oracle_expected_result) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":\"0x%0h\",\"actual\":\"0x%0h\"}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index, oracle_expected_result, result);
            $display("TEST_FAIL functional mismatch");
            $finish;
          end
          oracle_held_result = result;
        end else if (result_valid !== 1'b0) begin
          $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":\"no_output\",\"actual\":\"0x%0h\"}",
                   oracle_scenario_id, oracle_scenario_class, oracle_item_index, result);
          $display("TEST_FAIL unexpected output");
          $finish;
        end
        @(negedge clk);
        sample_valid = 1'b0;
        if (oracle_expected_record[RESULT_WIDTH]) begin
          if (oracle_stall_cycles > 0) begin
            sample = ~oracle_input_record[7:0];
            sample_valid = 1'b1;
            #1;
            if (sample_ready !== 1'b0) begin
              $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":\"ready=0\",\"actual\":\"ready=%0b\"}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index, sample_ready);
              $display("TEST_FAIL accepted sample while result stalled");
              $finish;
            end
          end
          for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
            @(posedge clk);
            #1;
            if (result_valid !== 1'b1 || result !== oracle_held_result) begin
              $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":\"0x%0h\",\"actual\":\"0x%0h\"}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index, oracle_held_result, result);
              $display("TEST_FAIL result changed under backpressure");
              $finish;
            end
          end
          @(negedge clk);
          sample_valid = 1'b0;
          result_ready = 1'b1;
          @(posedge clk);
          #1;
          if (result_valid !== 1'b0) begin
            $display("TEST_FAIL result_valid did not clear");
            $finish;
          end
        end
      end
      $display("TEST_PASS");
      $finish;
    end else begin
      repeat (2) @(posedge clk);
      rst_n = 1'b1;

      send_vector_and_expect(
        8'sd1, 8'sd2, 8'sd3, 8'sd4, 12'sd13
      );
      send_vector_and_expect(
        8'sd127, -8'sd128, 8'sd127, 8'sd127, 12'sd890
      );

      @(negedge clk);
      rst_n = 1'b0;
      repeat (2) @(posedge clk);
      @(negedge clk);
      rst_n = 1'b1;
      send_sample(8'sd5);
      send_sample(8'sd6);
      send_sample(8'sd7);
      @(negedge clk);
      result_ready = 1'b0;
      send_sample(8'sd8);
      if (result_valid !== 1'b1 || result !== 12'sd33) begin
        $display("TEST_FAIL failed to capture stalled result");
        $finish;
      end
      sample = 8'sd9;
      sample_valid = 1'b1;
      #1;
      if (sample_ready !== 1'b0) begin
        $display("TEST_FAIL accepted sample while result stalled");
        $finish;
      end
      repeat (2) begin
        @(posedge clk);
        #1;
        if (result_valid !== 1'b1 || result !== 12'sd33) begin
          $display("TEST_FAIL result changed under backpressure");
          $finish;
        end
      end
      @(negedge clk);
      sample_valid = 1'b0;
      result_ready = 1'b1;
      $display("TEST_PASS");
      $finish;
    end
  end
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
