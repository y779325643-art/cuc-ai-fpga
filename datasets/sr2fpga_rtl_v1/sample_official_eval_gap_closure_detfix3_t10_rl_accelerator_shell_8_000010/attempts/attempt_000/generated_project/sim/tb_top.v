`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg cfg_valid;
  wire cfg_ready;
  reg [2:0] cfg_addr;
  reg [7:0] cfg_data;
  reg sample_valid;
  wire sample_ready;
  reg [7:0] obs0;
  reg [7:0] obs1;
  reg [7:0] reward;
  reg [7:0] next_value;
  reg done_in;
  wire result_valid;
  reg result_ready;
  wire selected_action;
  wire [7:0] value_estimate;
  wire [7:0] updated_value;
  wire episode_done;
  wire irq;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .cfg_valid(cfg_valid),
    .cfg_ready(cfg_ready),
    .cfg_addr(cfg_addr),
    .cfg_data(cfg_data),
    .sample_valid(sample_valid),
    .sample_ready(sample_ready),
    .obs0(obs0),
    .obs1(obs1),
    .reward(reward),
    .next_value(next_value),
    .done_in(done_in),
    .result_valid(result_valid),
    .result_ready(result_ready),
    .selected_action(selected_action),
    .value_estimate(value_estimate),
    .updated_value(updated_value),
    .episode_done(episode_done),
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

  task send_sample;
    input [7:0] obs0_i;
    input [7:0] obs1_i;
    input [7:0] reward_i;
    input [7:0] next_value_i;
    input done_i;
    begin
      @(negedge clk);
      sample_valid = 1'b1;
      obs0 = obs0_i;
      obs1 = obs1_i;
      reward = reward_i;
      next_value = next_value_i;
      done_in = done_i;
      while (!sample_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      sample_valid = 1'b0;
    end
  endtask

  task expect_result;
    input expected_action;
    input [7:0] expected_value;
    input [7:0] expected_updated;
    input expected_done;
    begin
      wait_cycles = 0;
      while (!result_valid && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (!result_valid) begin
        $display("TEST_FAIL result did not become valid");
        $finish;
      end
      if (selected_action !== expected_action ||
          value_estimate !== expected_value ||
          updated_value !== expected_updated ||
          episode_done !== expected_done) begin
        $display("TEST_FAIL expected action=%0d value=%0d updated=%0d done=%0d got action=%0d value=%0d updated=%0d done=%0d",
                 expected_action, expected_value, expected_updated, expected_done,
                 selected_action, value_estimate, updated_value, episode_done);
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
    sample_valid = 1'b0;
    obs0 = 8'd0;
    obs1 = 8'd0;
    reward = 8'd0;
    next_value = 8'd0;
    done_in = 1'b0;
    result_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    write_cfg(3'd0, 8'd2);
    write_cfg(3'd1, 8'd1);
    write_cfg(3'd2, 8'd3);
    write_cfg(3'd3, 8'd0);
    write_cfg(3'd4, 8'd4);
    write_cfg(3'd5, 8'd1);

    send_sample(8'd4, 8'd2, 8'd1, 8'd8, 1'b0);
    expect_result(1'b0, 8'd7, 8'd7, 1'b0);

    send_sample(8'd1, 8'd5, 8'd2, 8'd15, 1'b1);
    expect_result(1'b1, 8'd9, 8'd11, 1'b1);

    if (irq !== 1'b1) begin
      $display("TEST_FAIL expected irq after done result");
      $finish;
    end

    $display("TEST_PASS");
    $finish;
  end
endmodule
