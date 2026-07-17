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
string oracle_input_path;
string oracle_expected_path;
string oracle_scenario_id;
string oracle_scenario_class;
integer oracle_transaction_count;
integer oracle_mode;
reg [42:0] oracle_input_memory [0:4095];
reg [15:0] oracle_expected_memory [0:4095];
reg [42:0] oracle_input_record;
reg [15:0] oracle_expected_record;
reg signed [7:0] oracle_held_error;
reg signed [7:0] oracle_held_value;
integer oracle_wait_count;
integer oracle_stall_index;
integer oracle_stall_cycles;

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


task run_td_oracle_scenario;
  integer oracle_item_index;
  begin
    if (oracle_transaction_count <= 0 || oracle_transaction_count > 4096) begin
      $display("ORACLE_ERROR invalid RL TD transaction count=%0d", oracle_transaction_count);
      $finish;
    end
    $readmemh(oracle_input_path, oracle_input_memory, 0, oracle_transaction_count - 1);
    $readmemh(oracle_expected_path, oracle_expected_memory, 0, oracle_transaction_count - 1);
    rst_n = 1'b0;
    in_valid = 1'b0;
    reward = 8'sd0;
    value = 8'sd0;
    next_value = 8'sd0;
    gamma = 8'd0;
    alpha = 8'd0;
    out_ready = 1'b0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count;
         oracle_item_index = oracle_item_index + 1) begin
      oracle_input_record = oracle_input_memory[oracle_item_index];
      oracle_expected_record = oracle_expected_memory[oracle_item_index];
      if (oracle_input_record[40]) begin
        @(negedge clk);
        rst_n = 1'b0;
        in_valid = 1'b0;
        out_ready = 1'b0;
        repeat (2) @(posedge clk);
        if (out_valid !== 1'b0) begin
          $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"reset_out_valid\",\"expected\":0,\"actual\":\"%0b\"}",
                   oracle_scenario_id, oracle_scenario_class, oracle_item_index, out_valid);
          $display("TEST_FAIL reset did not clear output valid");
          $finish;
        end
        @(negedge clk);
        rst_n = 1'b1;
      end
      out_ready = 1'b0;
      in_valid = 1'b1;
      reward = oracle_input_record[7:0];
      value = oracle_input_record[15:8];
      next_value = oracle_input_record[23:16];
      gamma = oracle_input_record[31:24];
      alpha = oracle_input_record[39:32];
      oracle_wait_count = 0;
      while (in_ready !== 1'b1 && oracle_wait_count < 500) begin
        @(negedge clk);
        oracle_wait_count = oracle_wait_count + 1;
      end
      if (in_ready !== 1'b1) begin
        $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"in_ready\",\"expected\":1,\"actual\":\"%0b\"}",
                 oracle_scenario_id, oracle_scenario_class, oracle_item_index, in_ready);
        $display("TEST_FAIL input timeout");
        $finish;
      end
      @(posedge clk);
      @(negedge clk);
      in_valid = 1'b0;
      oracle_wait_count = 0;
      while (out_valid !== 1'b1 && oracle_wait_count < 500) begin
        @(posedge clk);
        #1;
        oracle_wait_count = oracle_wait_count + 1;
      end
      if (out_valid !== 1'b1) begin
        $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"out_valid\",\"expected\":1,\"actual\":\"%0b\"}",
                 oracle_scenario_id, oracle_scenario_class, oracle_item_index, out_valid);
        $display("TEST_FAIL output timeout");
        $finish;
      end
      if (td_error !== oracle_expected_record[7:0] ||
          updated_value !== oracle_expected_record[15:8]) begin
        $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"td_error\":%0d,\"updated_value\":%0d},\"actual\":{\"td_error\":%0d,\"updated_value\":%0d}}",
                 oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                 $signed(oracle_expected_record[7:0]),
                 $signed(oracle_expected_record[15:8]),
                 td_error, updated_value);
        $display("TEST_FAIL functional mismatch");
        $finish;
      end
      oracle_held_error = td_error;
      oracle_held_value = updated_value;
      oracle_stall_cycles = oracle_input_record[42:41];
      if (oracle_stall_cycles > 0) begin
        for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles;
             oracle_stall_index = oracle_stall_index + 1) begin
          @(posedge clk);
          #1;
          if (td_error !== oracle_held_error || updated_value !== oracle_held_value ||
              out_valid !== 1'b1) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_stability\",\"expected\":\"stable\",\"actual\":\"changed\"}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index);
            $display("TEST_FAIL output changed under stall");
            $finish;
          end
        end
      end
      out_ready = 1'b1;
      @(posedge clk);
      #1;
      @(negedge clk);
      out_ready = 1'b0;
    end
    $display("TEST_PASS");
    $finish;
  end
endtask

  initial begin
    rst_n = 1'b0;
oracle_mode = $value$plusargs("ORACLE_INPUT=%s", oracle_input_path) &&
    $value$plusargs("ORACLE_EXPECTED=%s", oracle_expected_path) &&
    $value$plusargs("ORACLE_SCENARIO_ID=%s", oracle_scenario_id) &&
    $value$plusargs("ORACLE_SCENARIO_CLASS=%s", oracle_scenario_class) &&
    $value$plusargs("ORACLE_TRANSACTION_COUNT=%d", oracle_transaction_count);
if (oracle_mode) begin
  run_td_oracle_scenario;
end
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
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
