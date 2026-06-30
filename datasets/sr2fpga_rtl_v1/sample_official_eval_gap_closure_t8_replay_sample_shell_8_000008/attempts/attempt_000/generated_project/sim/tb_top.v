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
  wire sample_valid;
  reg sample_ready;
  wire [7:0] sample_state;
  wire sample_action;
  wire [7:0] sample_reward;
  wire [7:0] sample_next_state;
  wire sample_done;
  wire [2:0] occupancy;
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
    .sample_valid(sample_valid),
    .sample_ready(sample_ready),
    .sample_state(sample_state),
    .sample_action(sample_action),
    .sample_reward(sample_reward),
    .sample_next_state(sample_next_state),
    .sample_done(sample_done),
    .occupancy(occupancy)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task write_sample;
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

  task expect_sample;
    input [7:0] expected_state;
    input expected_action;
    input [7:0] expected_reward;
    input [7:0] expected_next_state;
    input expected_done;
    begin
      wait_cycles = 0;
      while (sample_valid !== 1'b1 && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (sample_valid !== 1'b1) begin
        $display("TEST_FAIL sample output did not become valid");
        $finish;
      end
      if (
        sample_state !== expected_state ||
        sample_action !== expected_action ||
        sample_reward !== expected_reward ||
        sample_next_state !== expected_next_state ||
        sample_done !== expected_done
      ) begin
        $display(
          "TEST_FAIL expected s=%0d a=%0d r=%0d ns=%0d d=%0d got s=%0d a=%0d r=%0d ns=%0d d=%0d",
          expected_state,
          expected_action,
          expected_reward,
          expected_next_state,
          expected_done,
          sample_state,
          sample_action,
          sample_reward,
          sample_next_state,
          sample_done
        );
        $finish;
      end
      @(posedge clk);
      #1;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    host_valid = 1'b0;
    host_state = 8'd0;
    host_action = 1'b0;
    host_reward = 8'd0;
    host_next_state = 8'd0;
    host_done = 1'b0;
    sample_ready = 1'b0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    write_sample(8'd3, 1'b1, 8'd4, 8'd5, 1'b0);
    write_sample(8'd8, 1'b0, 8'd2, 8'd9, 1'b1);
    write_sample(8'd1, 1'b1, 8'd7, 8'd6, 1'b0);
    @(posedge clk);
    #1;
    if (occupancy !== 3'd3) begin
      $display("TEST_FAIL expected occupancy 3 got %0d", occupancy);
      $finish;
    end

    sample_ready = 1'b1;
    expect_sample(8'd3, 1'b1, 8'd4, 8'd5, 1'b0);
    expect_sample(8'd8, 1'b0, 8'd2, 8'd9, 1'b1);
    expect_sample(8'd1, 1'b1, 8'd7, 8'd6, 1'b0);
    @(posedge clk);
    #1;
    if (occupancy !== 3'd0) begin
      $display("TEST_FAIL expected occupancy 0 got %0d", occupancy);
      $finish;
    end

    $display("TEST_PASS");
    $finish;
  end
endmodule
