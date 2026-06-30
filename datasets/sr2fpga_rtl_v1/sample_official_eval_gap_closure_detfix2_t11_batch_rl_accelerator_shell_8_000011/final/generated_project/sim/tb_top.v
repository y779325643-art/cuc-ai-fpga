`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg cfg_valid;
  wire cfg_ready;
  reg [2:0] cfg_addr;
  reg [7:0] cfg_data;
  reg batch_valid;
  wire batch_ready;
  reg [7:0] obs0_a;
  reg [7:0] obs1_a;
  reg [7:0] reward_a;
  reg [7:0] next_value_a;
  reg done_a;
  reg [7:0] obs0_b;
  reg [7:0] obs1_b;
  reg [7:0] reward_b;
  reg [7:0] next_value_b;
  reg done_b;
  wire result_valid;
  reg result_ready;
  wire selected_action_a;
  wire [7:0] value_estimate_a;
  wire [7:0] updated_value_a;
  wire selected_action_b;
  wire [7:0] value_estimate_b;
  wire [7:0] updated_value_b;
  wire batch_done;
  wire irq;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .cfg_valid(cfg_valid),
    .cfg_ready(cfg_ready),
    .cfg_addr(cfg_addr),
    .cfg_data(cfg_data),
    .batch_valid(batch_valid),
    .batch_ready(batch_ready),
    .obs0_a(obs0_a),
    .obs1_a(obs1_a),
    .reward_a(reward_a),
    .next_value_a(next_value_a),
    .done_a(done_a),
    .obs0_b(obs0_b),
    .obs1_b(obs1_b),
    .reward_b(reward_b),
    .next_value_b(next_value_b),
    .done_b(done_b),
    .result_valid(result_valid),
    .result_ready(result_ready),
    .selected_action_a(selected_action_a),
    .value_estimate_a(value_estimate_a),
    .updated_value_a(updated_value_a),
    .selected_action_b(selected_action_b),
    .value_estimate_b(value_estimate_b),
    .updated_value_b(updated_value_b),
    .batch_done(batch_done),
    .irq(irq)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task write_cfg;
    input [2:0] addr_i;
    input [7:0] data_i;
    begin
      @(negedge clk);
      cfg_valid = 1'b1;
      cfg_addr = addr_i;
      cfg_data = data_i;
      while (!cfg_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      cfg_valid = 1'b0;
    end
  endtask

  task send_batch;
    begin
      @(negedge clk);
      batch_valid = 1'b1;
      obs0_a = 8'd4;
      obs1_a = 8'd2;
      reward_a = 8'd1;
      next_value_a = 8'd8;
      done_a = 1'b0;
      obs0_b = 8'd1;
      obs1_b = 8'd5;
      reward_b = 8'd2;
      next_value_b = 8'd15;
      done_b = 1'b1;
      while (!batch_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      batch_valid = 1'b0;
    end
  endtask

  task expect_batch_result;
    input expected_action_a;
    input [7:0] expected_value_a;
    input [7:0] expected_updated_a;
    input expected_action_b;
    input [7:0] expected_value_b;
    input [7:0] expected_updated_b;
    input expected_batch_done;
    begin
      wait_cycles = 0;
      while (!result_valid && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (!result_valid) begin
        $display("TEST_FAIL batch result did not become valid");
        $finish;
      end
      if (selected_action_a !== expected_action_a ||
          value_estimate_a !== expected_value_a ||
          updated_value_a !== expected_updated_a ||
          selected_action_b !== expected_action_b ||
          value_estimate_b !== expected_value_b ||
          updated_value_b !== expected_updated_b ||
          batch_done !== expected_batch_done) begin
        $display("TEST_FAIL unexpected batch result");
        $finish;
      end
      @(posedge clk);
      #1;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    cfg_valid = 1'b0;
    cfg_addr = 3'd0;
    cfg_data = 8'd0;
    batch_valid = 1'b0;
    obs0_a = 8'd0;
    obs1_a = 8'd0;
    reward_a = 8'd0;
    next_value_a = 8'd0;
    done_a = 1'b0;
    obs0_b = 8'd0;
    obs1_b = 8'd0;
    reward_b = 8'd0;
    next_value_b = 8'd0;
    done_b = 1'b0;
    result_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    write_cfg(3'd0, 8'd2);
    write_cfg(3'd1, 8'd1);
    write_cfg(3'd2, 8'd3);
    write_cfg(3'd3, 8'd0);
    write_cfg(3'd4, 8'd4);
    write_cfg(3'd5, 8'd1);

    send_batch();
    expect_batch_result(1'b0, 8'd7, 8'd7, 1'b1, 8'd9, 8'd11, 1'b1);

    if (irq !== 1'b1) begin
      $display("TEST_FAIL expected irq after batch done result");
      $finish;
    end

    $display("TEST_PASS");
    $finish;
  end
endmodule
