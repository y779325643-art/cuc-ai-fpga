`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg cfg_valid;
  wire cfg_ready;
  reg [2:0] cfg_addr;
  reg [7:0] cfg_data;
  reg obs_valid;
  wire obs_ready;
  reg [7:0] obs0;
  reg [7:0] obs1;
  wire action_valid;
  reg action_ready;
  wire selected_action;
  wire [7:0] value_estimate;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .cfg_valid(cfg_valid),
    .cfg_ready(cfg_ready),
    .cfg_addr(cfg_addr),
    .cfg_data(cfg_data),
    .obs_valid(obs_valid),
    .obs_ready(obs_ready),
    .obs0(obs0),
    .obs1(obs1),
    .action_valid(action_valid),
    .action_ready(action_ready),
    .selected_action(selected_action),
    .value_estimate(value_estimate)
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

  task send_observation;
    input [7:0] obs0_i;
    input [7:0] obs1_i;
    begin
      @(negedge clk);
      obs_valid = 1'b1;
      obs0 = obs0_i;
      obs1 = obs1_i;
      while (!obs_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      obs_valid = 1'b0;
    end
  endtask

  task expect_action;
    input expected_action;
    input [7:0] expected_value;
    begin
      wait_cycles = 0;
      while (action_valid !== 1'b1 && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (action_valid !== 1'b1) begin
        $display("TEST_FAIL action output did not become valid");
        $finish;
      end
      if (selected_action !== expected_action || value_estimate !== expected_value) begin
        $display(
          "TEST_FAIL expected action=%0d value=%0d got action=%0d value=%0d",
          expected_action,
          expected_value,
          selected_action,
          value_estimate
        );
        $finish;
      end
      @(negedge clk);
    end
  endtask

  initial begin
    rst_n = 1'b0;
    cfg_valid = 1'b0;
    cfg_addr = 3'd0;
    cfg_data = 8'd0;
    obs_valid = 1'b0;
    obs0 = 8'd0;
    obs1 = 8'd0;
    action_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    write_cfg(3'd0, 8'd2);
    write_cfg(3'd1, 8'd1);
    write_cfg(3'd2, 8'd3);
    write_cfg(3'd3, 8'd0);
    write_cfg(3'd4, 8'd1);

    send_observation(8'd4, 8'd2);
    expect_action(1'b0, 8'd7);

    send_observation(8'd1, 8'd5);
    expect_action(1'b1, 8'd9);

    $display("TEST_PASS");
    $finish;
  end
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
