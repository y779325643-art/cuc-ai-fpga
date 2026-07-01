`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg host_valid;
  wire host_ready;
  reg [7:0] host_state;
  reg host_action;
  reg [7:0] host_reward;
  reg [7:0] host_next_state;
  reg host_done;
  reg sample_req_valid;
  wire sample_req_ready;
  reg [1:0] sample_index;
  wire sample_valid;
  reg sample_ready;
  wire [7:0] sample_state;
  wire sample_action;
  wire [7:0] sample_reward;
  wire [7:0] sample_next_state;
  wire sample_done;
  wire [2:0] occupancy;
  wire [1:0] write_index;
  wire irq;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .host_valid(host_valid),
    .host_ready(host_ready),
    .host_state(host_state),
    .host_action(host_action),
    .host_reward(host_reward),
    .host_next_state(host_next_state),
    .host_done(host_done),
    .sample_req_valid(sample_req_valid),
    .sample_req_ready(sample_req_ready),
    .sample_index(sample_index),
    .sample_valid(sample_valid),
    .sample_ready(sample_ready),
    .sample_state(sample_state),
    .sample_action(sample_action),
    .sample_reward(sample_reward),
    .sample_next_state(sample_next_state),
    .sample_done(sample_done),
    .occupancy(occupancy),
    .write_index(write_index),
    .irq(irq)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task write_host_packet;
    input [7:0] state_i;
    input action_i;
    input [7:0] reward_i;
    input [7:0] next_state_i;
    input done_i;
    begin
      @(negedge clk);
      host_valid = 1'b1;
      host_state = state_i;
      host_action = action_i;
      host_reward = reward_i;
      host_next_state = next_state_i;
      host_done = done_i;
      while (!host_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      host_valid = 1'b0;
    end
  endtask

  task request_sample;
    input [1:0] index_i;
    begin
      @(negedge clk);
      sample_req_valid = 1'b1;
      sample_index = index_i;
      while (!sample_req_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      sample_req_valid = 1'b0;
    end
  endtask

  task expect_sample;
    input [7:0] expected_state;
    input expected_action;
    input [7:0] expected_reward;
    input [7:0] expected_next_state;
    input expected_done;
    begin
      wait_cycles = 0;
      while (!sample_valid && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (!sample_valid) begin
        $display("TEST_FAIL sample did not become valid");
        $finish;
      end
      if (sample_state !== expected_state ||
          sample_action !== expected_action ||
          sample_reward !== expected_reward ||
          sample_next_state !== expected_next_state ||
          sample_done !== expected_done) begin
        $display("TEST_FAIL unexpected sample packet");
        $finish;
      end
      @(posedge clk);
      #1;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    host_valid = 1'b0;
    host_state = 8'h00;
    host_action = 1'b0;
    host_reward = 8'h00;
    host_next_state = 8'h00;
    host_done = 1'b0;
    sample_req_valid = 1'b0;
    sample_index = 2'd0;
    sample_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    write_host_packet(8'h12, 1'b0, 8'h03, 8'h21, 1'b0);
    write_host_packet(8'h34, 1'b1, 8'h05, 8'h43, 1'b1);

    if (occupancy !== 3'd2 || write_index !== 2'd2) begin
      $display("TEST_FAIL expected occupancy=2 write_index=2");
      $finish;
    end

    request_sample(2'd0);
    expect_sample(8'h12, 1'b0, 8'h03, 8'h21, 1'b0);

    request_sample(2'd1);
    expect_sample(8'h34, 1'b1, 8'h05, 8'h43, 1'b1);

    if (irq !== 1'b1) begin
      $display("TEST_FAIL expected irq after sample accepted");
      $finish;
    end

    $display("TEST_PASS");
    $finish;
  end
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
