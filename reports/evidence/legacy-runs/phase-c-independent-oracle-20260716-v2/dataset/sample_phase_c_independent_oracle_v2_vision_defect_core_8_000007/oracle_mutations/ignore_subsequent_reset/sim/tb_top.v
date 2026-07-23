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
  wire out_last;
  wire defect_present;
  wire [15:0] first_defect_x;
  wire [15:0] first_defect_y;
  reg expected_edge [0:24];
  integer output_count;
  integer i;
  integer timeout_count;
  integer expected_defect;
  integer expected_x;
  integer expected_y;
  reg frame_complete;
  reg scoreboard_enable;
  reg holding_output;
  reg held_edge;
  reg held_last;
  reg held_defect;
  reg [15:0] held_x;
  reg [15:0] held_y;
string oracle_input_path;
string oracle_expected_path;
string oracle_scenario_id;
string oracle_scenario_class;
integer oracle_transaction_count;
integer oracle_mode;
reg oracle_active;
reg [23:0] oracle_input_memory [0:4095];
reg [35:0] oracle_expected_memory [0:4095];
reg [23:0] oracle_input_record;
integer oracle_output_index;
integer oracle_expected_output_count;
integer oracle_expected_final_frame_count;
integer oracle_frame_output_count;
integer oracle_wait_count;
integer oracle_stall_index;
integer oracle_stall_cycles;
integer oracle_drain_target;
localparam integer ORACLE_EXPECT_OUTPUT_BIT = 35;
localparam integer ORACLE_OUT_LAST_BIT = 1;

  top dut (
    .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready),
    .in_pixel(in_pixel), .in_last(in_last), .out_valid(out_valid),
    .out_ready(out_ready), .out_edge(out_edge), .out_last(out_last),
    .defect_present(defect_present), .first_defect_x(first_defect_x), .first_defect_y(first_defect_y)
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
        out_last !== oracle_expected_memory[oracle_output_index][1] ||
        (oracle_expected_memory[oracle_output_index][1] &&
         (defect_present !== oracle_expected_memory[oracle_output_index][2] ||
          first_defect_x !== oracle_expected_memory[oracle_output_index][18:3] ||
          first_defect_y !== oracle_expected_memory[oracle_output_index][34:19]))) begin
      $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{\"edge\":%0d,\"out_last\":%0d,\"defect_present\":%0d,\"first_x\":%0d,\"first_y\":%0d},\"actual\":{\"edge\":\"%0b\",\"out_last\":\"%0b\",\"defect_present\":\"%0b\",\"first_x\":%0d,\"first_y\":%0d}}",
               oracle_scenario_id, oracle_scenario_class, oracle_output_index,
               oracle_expected_memory[oracle_output_index][0], oracle_expected_memory[oracle_output_index][1],
               oracle_expected_memory[oracle_output_index][2], oracle_expected_memory[oracle_output_index][18:3],
               oracle_expected_memory[oracle_output_index][34:19], out_edge, out_last, defect_present,
               first_defect_x, first_defect_y);
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
      if (holding_output && ((out_edge !== held_edge) || (out_last !== held_last) ||
          (defect_present !== held_defect) || (first_defect_x !== held_x) || (first_defect_y !== held_y))) begin
if (oracle_active) begin
  $display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_stability\",\"expected\":\"stable\",\"actual\":\"changed\"}",
           oracle_scenario_id, oracle_scenario_class, oracle_output_index);
end
        $display("TEST_FAIL output changed under stall");
        $finish;
      end
      holding_output <= 1'b1;
      held_edge <= out_edge;
      held_last <= out_last;
      held_defect <= defect_present;
      held_x <= first_defect_x;
      held_y <= first_defect_y;
    end else begin
      holding_output <= 1'b0;
    end
  end

  always @(posedge clk) begin
    if (rst_n && scoreboard_enable && out_valid && out_ready) begin
      if (output_count >= 25 || out_edge !== expected_edge[output_count]) begin
        $display("TEST_FAIL edge index=%0d expected=%0d actual=%0d", output_count, expected_edge[output_count], out_edge);
        $finish;
      end
      if (out_last !== (output_count == 24)) begin
        $display("TEST_FAIL last index=%0d actual=%0d", output_count, out_last);
        $finish;
      end
      if (out_last) begin
        if (defect_present !== expected_defect || first_defect_x !== expected_x || first_defect_y !== expected_y) begin
          $display("TEST_FAIL frame report expected present=%0d x=%0d y=%0d actual present=%0d x=%0d y=%0d",
            expected_defect, expected_x, expected_y, defect_present, first_defect_x, first_defect_y);
          $finish;
        end
        frame_complete = 1'b1;
      end
      output_count = output_count + 1;
    end
  end

  task clear_expected;
    begin
      for (i = 0; i < 25; i = i + 1) expected_edge[i] = 1'b0;
    end
  endtask

  task load_vertical_expected;
    begin
      clear_expected;
      expected_edge[6] = 1'b1; expected_edge[7] = 1'b1;
      expected_edge[11] = 1'b1; expected_edge[12] = 1'b1;
      expected_edge[16] = 1'b1; expected_edge[17] = 1'b1;
    end
  endtask

  task load_horizontal_expected;
    begin
      clear_expected;
      expected_edge[6] = 1'b1; expected_edge[7] = 1'b1; expected_edge[8] = 1'b1;
      expected_edge[11] = 1'b1; expected_edge[12] = 1'b1; expected_edge[13] = 1'b1;
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
      while (!(in_valid && in_ready)) @(posedge clk);
      @(negedge clk);
      in_valid = 1'b0;
      in_pixel = 8'd0;
      in_last = 1'b0;
    end
  endtask

  task send_frame;
    input integer image_mode;
    input [7:0] level;
    integer row;
    integer column;
    reg [7:0] pixel;
    begin
      for (row = 0; row < 5; row = row + 1) begin
        for (column = 0; column < 5; column = column + 1) begin
          pixel = 8'd0;
          if (image_mode == 1 && column >= 2) pixel = level;
          if (image_mode == 2 && row >= 2) pixel = level;
          send_pixel(pixel, row == 4 && column == 4);
        end
      end
    end
  endtask

  task reset_dut;
    begin
      @(negedge clk);
      rst_n = 1'b0;
      in_valid = 1'b0;
      in_pixel = 8'd0;
      in_last = 1'b0;
      out_ready = 1'b1;
      repeat (2) @(posedge clk);
      @(negedge clk);
      rst_n = 1'b1;
    end
  endtask

  task wait_for_frame;
    begin
      timeout_count = 0;
      while (!frame_complete && timeout_count < 300) begin
        @(posedge clk);
        timeout_count = timeout_count + 1;
      end
      if (!frame_complete || output_count != 25) begin
        $display("TEST_FAIL timeout outputs=%0d complete=%0d", output_count, frame_complete);
        $finish;
      end
      @(negedge clk);
    end
  endtask

  task run_frame;
    input integer image_mode;
    input [7:0] level;
    input integer expected_present;
    input integer first_x;
    input integer first_y;
    input integer inject_stall;
    begin
      if (image_mode == 1) load_vertical_expected;
      else if (image_mode == 2) load_horizontal_expected;
      else clear_expected;
      output_count = 0;
      frame_complete = 1'b0;
      expected_defect = expected_present;
      expected_x = first_x;
      expected_y = first_y;
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
            send_frame(image_mode, level);
          end
        join
      end else begin
        send_frame(image_mode, level);
      end
      wait_for_frame;
      scoreboard_enable = 1'b0;
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
    scoreboard_enable = 1'b0;
    holding_output = 1'b0;
    clear_expected;
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;

    run_frame(0, 8'd0, 0, 0, 0, 0);
    // A 25-level vertical step reaches the exact >= threshold of 100.
    run_frame(1, 8'd25, 1, 1, 1, 1);
    // A horizontal exact-threshold step makes the two line-buffer row order observable.
    run_frame(2, 8'd25, 1, 1, 1, 0);
    // No reset separates this second frame from the previous completed frame.
    run_frame(1, 8'd25, 1, 1, 1, 0);

    scoreboard_enable = 1'b0;
    send_pixel(8'd0, 1'b0);
    send_pixel(8'd0, 1'b0);
    send_pixel(8'd0, 1'b0);
    reset_dut;
    run_frame(0, 8'd0, 0, 0, 0, 0);

    $display("TEST_PASS");
    $finish;
  end

  initial begin
    #8000;
    $display("TEST_FAIL timeout");
    $finish;
  end
endmodule
