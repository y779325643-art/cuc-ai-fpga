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
string oracle_input_path;
string oracle_expected_path;
string oracle_scenario_id;
string oracle_scenario_class;
integer oracle_transaction_count;
integer oracle_mode;
reg [47:0] oracle_input_memory [0:4095];
reg [19:0] oracle_expected_memory [0:4095];
reg [47:0] oracle_input_record;
reg [19:0] oracle_expected_record;
reg oracle_held_action;
reg [7:0] oracle_held_value;
reg [7:0] oracle_held_updated;
reg oracle_held_done;
integer oracle_wait_count;
integer oracle_stall_index;
integer oracle_stall_cycles;

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


task run_rl_oracle_scenario;
  integer oracle_item_index;
  begin
    if (oracle_transaction_count <= 0 || oracle_transaction_count > 4096) begin
      $display("ORACLE_ERROR invalid RL accelerator transaction count=%0d", oracle_transaction_count);
      $finish;
    end
    $readmemh(oracle_input_path, oracle_input_memory, 0, oracle_transaction_count - 1);
    $readmemh(oracle_expected_path, oracle_expected_memory, 0, oracle_transaction_count - 1);
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
    result_ready = 1'b0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count;
         oracle_item_index = oracle_item_index + 1) begin
      oracle_input_record = oracle_input_memory[oracle_item_index];
      oracle_expected_record = oracle_expected_memory[oracle_item_index];
      case (oracle_input_record[1:0])
        2'd0: begin
          @(negedge clk);
          rst_n = 1'b0;
          cfg_valid = 1'b0;
          sample_valid = 1'b0;
          result_ready = 1'b0;
          repeat (2) @(posedge clk);
          #1;
          if (result_valid !== 1'b0 || irq !== oracle_expected_record[19]) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"reset_state\",\"expected\":{\"result_valid\":0,\"irq\":%0d},\"actual\":{\"result_valid\":\"%0b\",\"irq\":\"%0b\"}}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                     oracle_expected_record[19], result_valid, irq);
            $display("TEST_FAIL reset did not clear result/irq");
            $finish;
          end
          @(negedge clk);
          rst_n = 1'b1;
        end
        2'd1: begin
          @(negedge clk);
          cfg_valid = 1'b1;
          cfg_addr = oracle_input_record[4:2];
          cfg_data = oracle_input_record[12:5];
          oracle_wait_count = 0;
          while (cfg_ready !== 1'b1 && oracle_wait_count < 500) begin
            @(negedge clk);
            oracle_wait_count = oracle_wait_count + 1;
          end
          if (cfg_ready !== 1'b1) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"cfg_ready\",\"expected\":1,\"actual\":\"%0b\"}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index, cfg_ready);
            $display("TEST_FAIL config timeout");
            $finish;
          end
          @(posedge clk);
          @(negedge clk);
          cfg_valid = 1'b0;
          if (irq !== oracle_expected_record[19]) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"irq_after_config\",\"expected\":%0d,\"actual\":\"%0b\"}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                     oracle_expected_record[19], irq);
            $display("TEST_FAIL irq changed on config write");
            $finish;
          end
        end
        2'd2: begin
          result_ready = 1'b0;
          @(negedge clk);
          sample_valid = 1'b1;
          obs0 = oracle_input_record[20:13];
          obs1 = oracle_input_record[28:21];
          reward = oracle_input_record[36:29];
          next_value = oracle_input_record[44:37];
          done_in = oracle_input_record[45];
          oracle_wait_count = 0;
          while (sample_ready !== 1'b1 && oracle_wait_count < 500) begin
            @(negedge clk);
            oracle_wait_count = oracle_wait_count + 1;
          end
          if (sample_ready !== 1'b1) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"sample_ready\",\"expected\":1,\"actual\":\"%0b\"}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index, sample_ready);
            $display("TEST_FAIL sample timeout");
            $finish;
          end
          @(posedge clk);
          @(negedge clk);
          sample_valid = 1'b0;
          if (!oracle_expected_record[0]) begin
            repeat (8) begin
              @(posedge clk);
              #1;
              if (result_valid === 1'b1) begin
                $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"disabled_output\",\"expected\":0,\"actual\":1}",
                         oracle_scenario_id, oracle_scenario_class, oracle_item_index);
                $display("TEST_FAIL disabled accelerator emitted output");
                $finish;
              end
            end
            if (irq !== oracle_expected_record[19]) begin
              $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"disabled_irq\",\"expected\":%0d,\"actual\":\"%0b\"}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                       oracle_expected_record[19], irq);
              $display("TEST_FAIL disabled accelerator changed irq");
              $finish;
            end
          end else begin
            oracle_wait_count = 0;
            while (result_valid !== 1'b1 && oracle_wait_count < 500) begin
              @(posedge clk);
              #1;
              oracle_wait_count = oracle_wait_count + 1;
            end
            if (result_valid !== 1'b1) begin
              $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"result_valid\",\"expected\":1,\"actual\":\"%0b\"}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index, result_valid);
              $display("TEST_FAIL result timeout");
              $finish;
            end
            if (selected_action !== oracle_expected_record[1] ||
                value_estimate !== oracle_expected_record[9:2] ||
                updated_value !== oracle_expected_record[17:10] ||
                episode_done !== oracle_expected_record[18]) begin
              $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"selected_action\":%0d,\"value_estimate\":%0d,\"updated_value\":%0d,\"episode_done\":%0d},\"actual\":{\"selected_action\":\"%0b\",\"value_estimate\":%0d,\"updated_value\":%0d,\"episode_done\":\"%0b\"}}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                       oracle_expected_record[1],
                       oracle_expected_record[9:2],
                       oracle_expected_record[17:10],
                       oracle_expected_record[18],
                       selected_action, value_estimate, updated_value, episode_done);
              $display("TEST_FAIL functional mismatch");
              $finish;
            end
            oracle_held_action = selected_action;
            oracle_held_value = value_estimate;
            oracle_held_updated = updated_value;
            oracle_held_done = episode_done;
            oracle_stall_cycles = oracle_input_record[47:46];
            if (oracle_stall_cycles > 0) begin
              for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles;
                   oracle_stall_index = oracle_stall_index + 1) begin
                @(posedge clk);
                #1;
                if (selected_action !== oracle_held_action || value_estimate !== oracle_held_value ||
                    updated_value !== oracle_held_updated || episode_done !== oracle_held_done ||
                    result_valid !== 1'b1) begin
                  $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_stability\",\"expected\":\"stable\",\"actual\":\"changed\"}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index);
                  $display("TEST_FAIL output changed under stall");
                  $finish;
                end
              end
            end
            result_ready = 1'b1;
            @(posedge clk);
            #1;
            if (irq !== oracle_expected_record[19]) begin
              $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"irq\",\"expected\":%0d,\"actual\":\"%0b\"}",
                       oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                       oracle_expected_record[19], irq);
              $display("TEST_FAIL irq mismatch");
              $finish;
            end
            @(negedge clk);
            result_ready = 1'b0;
          end
        end
        default: begin
          $display("ORACLE_ERROR unsupported RL operation=%0d", oracle_input_record[1:0]);
          $finish;
        end
      endcase
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
  run_rl_oracle_scenario;
end
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
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
