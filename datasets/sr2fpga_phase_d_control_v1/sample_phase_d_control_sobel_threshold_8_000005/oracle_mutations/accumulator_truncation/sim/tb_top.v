`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [7:0] in_pixel;
  reg in_last;
  wire out_valid;
  reg out_ready;
  wire out_edge;
  wire edge_axis;
  wire out_last;
  reg expected_edge [0:24];
  reg expected_axis [0:24];
  integer output_count;
  integer i;
  integer timeout_count;
  reg scoreboard_last_consumed;
  reg scoreboard_enable;
  reg holding_output;
  reg held_edge;
  reg held_axis;
  reg held_last;
string oracle_input_path;
string oracle_expected_path;
string oracle_scenario_id;
string oracle_scenario_class;
integer oracle_transaction_count;
integer oracle_mode;
reg oracle_active;
reg [23:0] oracle_input_memory [0:4095];
reg [3:0] oracle_expected_memory [0:4095];
reg [23:0] oracle_input_record;
integer oracle_output_index;
integer oracle_expected_output_count;
integer oracle_expected_final_frame_count;
integer oracle_frame_output_count;
integer oracle_wait_count;
integer oracle_stall_index;
integer oracle_stall_cycles;
integer oracle_drain_target;
localparam integer ORACLE_EXPECT_OUTPUT_BIT = 3;
localparam integer ORACLE_OUT_LAST_BIT = 2;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_pixel(in_pixel),
    .in_last(in_last),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_edge(out_edge),
    .edge_axis(edge_axis),
    .out_last(out_last)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

always @(posedge clk) begin
  if (rst_n && oracle_active && out_valid && out_ready) begin
    if (oracle_output_index >= oracle_expected_output_count || oracle_frame_output_count >= 25) begin
      $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_count\",\"expected\":\"at_most_25_per_frame\",\"actual\":\"overflow\"}",
               oracle_scenario_id, oracle_scenario_class, oracle_output_index);
      $display("TEST_FAIL emitted more than 25 pixels");
      $finish;
    end
    if (out_edge !== oracle_expected_memory[oracle_output_index][0] ||
        edge_axis !== oracle_expected_memory[oracle_output_index][1] ||
        out_last !== oracle_expected_memory[oracle_output_index][2]) begin
      $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"edge\":%0d,\"axis\":%0d,\"out_last\":%0d},\"actual\":{\"edge\":\"%0b\",\"axis\":\"%0b\",\"out_last\":\"%0b\"}}",
               oracle_scenario_id, oracle_scenario_class, oracle_output_index,
               oracle_expected_memory[oracle_output_index][0], oracle_expected_memory[oracle_output_index][1],
               oracle_expected_memory[oracle_output_index][2], out_edge, edge_axis, out_last);
      $display("TEST_FAIL functional mismatch");
      $finish;
    end
    oracle_output_index = oracle_output_index + 1;
    if (out_last) oracle_frame_output_count = 0;
    else oracle_frame_output_count = oracle_frame_output_count + 1;
  end
end

  always @(posedge clk) begin
    if (!rst_n) begin
      holding_output <= 1'b0;
    end else if (out_valid && !out_ready) begin
      if (holding_output && ((out_edge !== held_edge) || (edge_axis !== held_axis) || (out_last !== held_last))) begin
if (oracle_active) begin
  $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_stability\",\"expected\":\"stable\",\"actual\":\"changed\"}",
           oracle_scenario_id, oracle_scenario_class, oracle_output_index);
end
        $display("TEST_FAIL output changed under stall");
        $finish;
      end
      holding_output <= 1'b1;
      held_edge <= out_edge;
      held_axis <= edge_axis;
      held_last <= out_last;
    end else begin
      holding_output <= 1'b0;
    end
  end

  always @(posedge clk) begin
    if (rst_n && scoreboard_enable && out_valid && out_ready) begin
      if (output_count >= 25) begin
        $display("TEST_FAIL emitted more than 25 pixels");
        $finish;
      end
      if (out_edge !== expected_edge[output_count]) begin
        $display("TEST_FAIL edge index=%0d expected=%0d actual=%0d", output_count, expected_edge[output_count], out_edge);
        $finish;
      end
      if (edge_axis !== expected_axis[output_count]) begin
        $display("TEST_FAIL axis index=%0d expected=%0d actual=%0d", output_count, expected_axis[output_count], edge_axis);
        $finish;
      end
      if (out_last !== (output_count == 24)) begin
        $display("TEST_FAIL last index=%0d actual=%0d", output_count, out_last);
        $finish;
      end
      output_count = output_count + 1;
      if (out_last) begin
        scoreboard_last_consumed = 1'b1;
      end
    end
  end

  task clear_expected;
    begin
      for (i = 0; i < 25; i = i + 1) begin
        expected_edge[i] = 1'b0;
        expected_axis[i] = 1'b0;
      end
    end
  endtask

  task load_vertical_expected;
    begin
      clear_expected;
      expected_axis[6] = 1'b1; expected_axis[7] = 1'b1; expected_axis[8] = 1'b1;
      expected_axis[11] = 1'b1; expected_axis[12] = 1'b1; expected_axis[13] = 1'b1;
      expected_axis[16] = 1'b1; expected_axis[17] = 1'b1; expected_axis[18] = 1'b1;
      expected_edge[6] = 1'b1; expected_axis[6] = 1'b1;
      expected_edge[7] = 1'b1; expected_axis[7] = 1'b1;
      expected_edge[11] = 1'b1; expected_axis[11] = 1'b1;
      expected_edge[12] = 1'b1; expected_axis[12] = 1'b1;
      expected_edge[16] = 1'b1; expected_axis[16] = 1'b1;
      expected_edge[17] = 1'b1; expected_axis[17] = 1'b1;
    end
  endtask

  task load_flat_expected;
    begin
      clear_expected;
      // The documented >= tie rule makes a zero-gradient interior axis bit one.
      expected_axis[6] = 1'b1; expected_axis[7] = 1'b1; expected_axis[8] = 1'b1;
      expected_axis[11] = 1'b1; expected_axis[12] = 1'b1; expected_axis[13] = 1'b1;
      expected_axis[16] = 1'b1; expected_axis[17] = 1'b1; expected_axis[18] = 1'b1;
    end
  endtask

  task load_horizontal_expected;
    begin
      clear_expected;
      expected_edge[6] = 1'b1; expected_edge[7] = 1'b1; expected_edge[8] = 1'b1;
      expected_edge[11] = 1'b1; expected_edge[12] = 1'b1; expected_edge[13] = 1'b1;
      expected_axis[16] = 1'b1; expected_axis[17] = 1'b1; expected_axis[18] = 1'b1;
    end
  endtask

  task send_pixel;
    input [7:0] pixel;
    input last_pixel;
    begin
      @(negedge clk);
      in_valid = 1'b1;
      in_pixel = pixel;
      in_last = last_pixel;
      while (!(in_valid && in_ready)) begin
        @(posedge clk);
      end
      @(negedge clk);
      in_valid = 1'b0;
      in_pixel = 8'd0;
      in_last = 1'b0;
    end
  endtask

  task send_frame;
    input integer mode;
    input [7:0] level;
    integer row;
    integer column;
    reg [7:0] pixel;
    begin
      for (row = 0; row < 5; row = row + 1) begin
        for (column = 0; column < 5; column = column + 1) begin
          pixel = 8'd0;
          if (mode == 1 && column >= 2) pixel = level; // vertical edge
          if (mode == 2 && row >= 2) pixel = level; // horizontal edge
          send_pixel(pixel, row == 4 && column == 4);
        end
      end
    end
  endtask

  task wait_for_frame;
    begin
      timeout_count = 0;
      while (!scoreboard_last_consumed && timeout_count < 300) begin
        @(posedge clk);
        timeout_count = timeout_count + 1;
      end
      if (!scoreboard_last_consumed || output_count != 25) begin
        $display("TEST_FAIL timeout outputs=%0d last_consumed=%0d", output_count, scoreboard_last_consumed);
        $finish;
      end
      @(negedge clk);
    end
  endtask

  task send_frame_without_last;
    integer row;
    integer column;
    begin
      for (row = 0; row < 5; row = row + 1) begin
        for (column = 0; column < 5; column = column + 1) begin
          send_pixel(8'd0, 1'b0);
        end
      end
    end
  endtask

  task run_frame;
    input integer mode;
    input [7:0] level;
    input integer inject_stall;
    begin
      output_count = 0;
      scoreboard_last_consumed = 1'b0;
      scoreboard_enable = 1'b1;
      out_ready = 1'b1;
      if (inject_stall != 0) begin
        fork
          begin
            repeat (4) @(posedge clk);
            @(negedge clk);
            out_ready = 1'b0;
            repeat (3) @(posedge clk);
            @(negedge clk);
            out_ready = 1'b1;
          end
          begin
            send_frame(mode, level);
          end
        join
      end else begin
        send_frame(mode, level);
      end
      wait_for_frame;
    end
  endtask

task run_oracle_scenario;
  integer oracle_item_index;
  integer oracle_scan_index;
  begin
    if (oracle_transaction_count <= 0 || oracle_transaction_count > 4096) begin
      $display("ORACLE_ERROR invalid image transaction count=%0d", oracle_transaction_count);
      $finish;
    end
    $readmemh(oracle_input_path, oracle_input_memory, 0, oracle_transaction_count - 1);
    $readmemh(oracle_expected_path, oracle_expected_memory, 0, oracle_transaction_count - 1);
    oracle_expected_output_count = 0;
    oracle_expected_final_frame_count = 0;
    for (oracle_scan_index = 0; oracle_scan_index < oracle_transaction_count;
         oracle_scan_index = oracle_scan_index + 1) begin
      if (oracle_expected_memory[oracle_scan_index][ORACLE_EXPECT_OUTPUT_BIT]) begin
        oracle_expected_output_count = oracle_expected_output_count + 1;
        if (oracle_expected_memory[oracle_scan_index][ORACLE_OUT_LAST_BIT])
          oracle_expected_final_frame_count = 0;
        else
          oracle_expected_final_frame_count = oracle_expected_final_frame_count + 1;
      end
    end
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_pixel = 8'd0;
    in_last = 1'b0;
    out_ready = 1'b1;
    scoreboard_enable = 1'b0;
    holding_output = 1'b0;
    oracle_output_index = 0;
    oracle_frame_output_count = 0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count;
         oracle_item_index = oracle_item_index + 1) begin
      oracle_input_record = oracle_input_memory[oracle_item_index];
      if (oracle_input_record[9]) begin
        oracle_drain_target = oracle_input_record[23:12];
        if (oracle_drain_target < oracle_output_index ||
            oracle_drain_target > oracle_expected_output_count) begin
          $display("ORACLE_ERROR invalid reset drain target=%0d", oracle_drain_target);
          $finish;
        end
        oracle_wait_count = 0;
        while (oracle_output_index < oracle_drain_target && oracle_wait_count < 500) begin
          @(negedge clk);
          oracle_wait_count = oracle_wait_count + 1;
        end
        if (oracle_output_index != oracle_drain_target) begin
          $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"pre_reset_drain\",\"expected\":%0d,\"actual\":%0d}",
                   oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                   oracle_drain_target, oracle_output_index);
          $display("TEST_FAIL timeout before reset");
          $finish;
        end
        @(negedge clk);
        rst_n = 1'b0;
        in_valid = 1'b0;
        out_ready = 1'b1;
        repeat (2) @(posedge clk);
        @(negedge clk);
        oracle_frame_output_count = 0;
        rst_n = 1'b1;
      end
      @(negedge clk);
      in_pixel = oracle_input_record[7:0];
      in_last = oracle_input_record[8];
      in_valid = 1'b1;
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
      in_last = 1'b0;
      oracle_stall_cycles = oracle_input_record[11:10];
      if (oracle_stall_cycles > 0) begin
        if (oracle_item_index + 1 >= oracle_transaction_count ||
            oracle_input_memory[oracle_item_index + 1][9] ||
            oracle_input_memory[oracle_item_index + 1][7:0] == oracle_input_record[7:0]) begin
          $display("ORACLE_ERROR output stall requires a changed pending input pixel");
          $finish;
        end
        out_ready = 1'b0;
        in_pixel = oracle_input_memory[oracle_item_index + 1][7:0];
        in_last = oracle_input_memory[oracle_item_index + 1][8];
        in_valid = 1'b1;
        for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles;
             oracle_stall_index = oracle_stall_index + 1) begin
          @(posedge clk);
          if (out_valid !== 1'b1 || in_ready !== 1'b0) begin
            $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"input_backpressure\",\"expected\":0,\"actual\":\"%0b\"}",
                     oracle_scenario_id, oracle_scenario_class, oracle_item_index + 1, in_ready);
            $display("TEST_FAIL input accepted while output stalled");
            $finish;
          end
        end
        @(negedge clk);
        in_valid = 1'b0;
        in_last = 1'b0;
        out_ready = 1'b1;
      end
    end
    oracle_wait_count = 0;
    while (oracle_output_index < oracle_expected_output_count && oracle_wait_count < 1000) begin
      @(negedge clk);
      oracle_wait_count = oracle_wait_count + 1;
    end
    repeat (10) @(posedge clk);
    if (oracle_output_index != oracle_expected_output_count ||
        oracle_frame_output_count != oracle_expected_final_frame_count) begin
      $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_count\",\"expected\":%0d,\"actual\":%0d}",
               oracle_scenario_id, oracle_scenario_class, oracle_output_index,
               oracle_expected_output_count, oracle_output_index);
      $display("TEST_FAIL timeout outputs=%0d", oracle_output_index);
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endtask

  initial begin
    rst_n = 1'b0;
oracle_active = 1'b0;
oracle_mode = $value$plusargs("ORACLE_INPUT=%s", oracle_input_path) &&
    $value$plusargs("ORACLE_EXPECTED=%s", oracle_expected_path) &&
    $value$plusargs("ORACLE_SCENARIO_ID=%s", oracle_scenario_id) &&
    $value$plusargs("ORACLE_SCENARIO_CLASS=%s", oracle_scenario_class) &&
    $value$plusargs("ORACLE_TRANSACTION_COUNT=%d", oracle_transaction_count);
if (oracle_mode) begin
  oracle_active = 1'b1;
  run_oracle_scenario;
end
    in_valid = 1'b0;
    in_pixel = 8'd0;
    in_last = 1'b0;
    out_ready = 1'b1;
    output_count = 0;
    scoreboard_last_consumed = 1'b0;
    scoreboard_enable = 1'b0;
    holding_output = 1'b0;
    clear_expected;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    // Flat 5x5 frame and an output stall exercise zero borders and buffer stability.
    load_flat_expected;
    run_frame(0, 8'd0, 1);

    // A vertical edge has horizontal-gradient dominance, so edge_axis must be one.
    load_vertical_expected;
    run_frame(1, 8'd255, 0);

    // Exact threshold crossing: a 25-level vertical step has Sobel magnitude 100.
    load_vertical_expected;
    run_frame(1, 8'd25, 0);

    // A horizontal edge is the complementary axis case and must report edge_axis zero.
    load_horizontal_expected;
    run_frame(2, 8'd255, 0);

    // Without final in_last the last right-border output is not followed by bottom flush/out_last.
    scoreboard_enable = 1'b0;
    send_frame_without_last;
    repeat (20) @(posedge clk);
    if (out_last) begin
      $display("TEST_FAIL out_last emitted without final in_last");
      $finish;
    end
    @(negedge clk);
    rst_n = 1'b0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    load_flat_expected;
    run_frame(0, 8'd0, 0);

    // Reset during a partial frame must discard it and restart output ordering.
    scoreboard_enable = 1'b0;
    output_count = 0;
    scoreboard_last_consumed = 1'b0;
    send_pixel(8'd0, 1'b0);
    send_pixel(8'd0, 1'b0);
    send_pixel(8'd0, 1'b0);
    @(negedge clk);
    rst_n = 1'b0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    load_flat_expected;
    run_frame(0, 8'd0, 0);

    $display("TEST_PASS");
    $finish;
  end

  initial begin
    #30000;
    $display("TEST_FAIL global timeout");
    $finish;
  end
endmodule
