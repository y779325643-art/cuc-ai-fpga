"""Stable family metadata for datapath generator tasks."""

from textwrap import dedent

TASK_FAMILY_IDS = {
    "pwm_controller": "pwm_generator",
    "fir_filter": "fir_filter",
    "matrix_vector_mac": "matrix_vector_mac",
    "alu_control_unit": "alu_control_unit",
    "crc_stream_checker": "crc_stream_checker",
    "matched_filter": "matched_filter",
    "peak_detector": "peak_detector",
    "pulse_radar_signal": "p_pulse_radar_signal",
}


def matched_filter_testbench(width: int) -> str:
    acc_width = width * 2 + 2
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg signed [{width - 1}:0] in_sample;
          wire out_valid;
          reg out_ready;
          wire signed [{acc_width - 1}:0] correlation;
          reg signed [{acc_width - 1}:0] held_correlation;
          localparam INPUT_RECORD_WIDTH = {width + 3};
          localparam EXPECTED_RECORD_WIDTH = {acc_width};
          localparam MAX_ORACLE_TRANSACTIONS = 4096;
          reg [INPUT_RECORD_WIDTH-1:0] oracle_inputs [0:MAX_ORACLE_TRANSACTIONS-1];
          reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected [0:MAX_ORACLE_TRANSACTIONS-1];
          reg [INPUT_RECORD_WIDTH-1:0] oracle_input_record;
          reg signed [EXPECTED_RECORD_WIDTH-1:0] oracle_expected_correlation;
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
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_sample(in_sample),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .correlation(correlation)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_and_expect;
            input signed [{width - 1}:0] value;
            input signed [{acc_width - 1}:0] expected;
            begin
              @(negedge clk);
              while (in_ready !== 1'b1) begin
                @(negedge clk);
              end
              in_sample = value;
              in_valid = 1'b1;
              @(posedge clk);
              #1;
              if (out_valid !== 1'b1 || correlation !== expected) begin
                $display("TEST_FAIL correlation expected=%0d actual=%0d", expected, correlation);
                $finish;
              end
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task oracle_reset_dut;
            begin
              @(negedge clk);
              rst_n = 1'b0;
              in_valid = 1'b0;
              out_ready = 1'b1;
              repeat (2) @(posedge clk);
              @(negedge clk);
              rst_n = 1'b1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_sample = {width}'sd0;
            out_ready = 1'b1;
            held_correlation = {acc_width}'sd0;
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
              $readmemh(oracle_input_path, oracle_inputs, 0, oracle_transaction_count - 1);
              $readmemh(oracle_expected_path, oracle_expected, 0, oracle_transaction_count - 1);
              repeat (2) @(posedge clk);
              rst_n = 1'b1;
              for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count; oracle_item_index = oracle_item_index + 1) begin
                oracle_input_record = oracle_inputs[oracle_item_index];
                oracle_expected_correlation = oracle_expected[oracle_item_index];
                oracle_stall_cycles = oracle_input_record[{width + 2}:{width + 1}];
                if (oracle_input_record[{width}]) begin
                  oracle_reset_dut;
                end
                @(negedge clk);
                while (in_ready !== 1'b1) begin
                  @(negedge clk);
                end
                out_ready = oracle_stall_cycles == 0;
                in_sample = oracle_input_record[{width - 1}:0];
                in_valid = 1'b1;
                @(posedge clk);
                #1;
                if (out_valid !== 1'b1 || correlation !== oracle_expected_correlation) begin
                  $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"correlation\\\":\\\"0x%0h\\\"}},\\\"actual\\\":{{\\\"correlation\\\":\\\"0x%0h\\\",\\\"out_valid\\\":\\\"%0b\\\"}}}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index, oracle_expected_correlation, correlation, out_valid);
                  $display("TEST_FAIL functional mismatch");
                  $finish;
                end
                held_correlation = correlation;
                @(negedge clk);
                in_valid = 1'b0;
                if (oracle_stall_cycles > 0) begin
                  in_sample = ~oracle_input_record[{width - 1}:0];
                  in_valid = 1'b1;
                  #1;
                  if (in_ready !== 1'b0) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"in_ready\\\":0}},\\\"actual\\\":{{\\\"in_ready\\\":\\\"%0b\\\"}}}}",
                             oracle_scenario_id, oracle_scenario_class, oracle_item_index, in_ready);
                    $display("TEST_FAIL accepted sample while output stalled");
                    $finish;
                  end
                end
                for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
                  @(posedge clk);
                  #1;
                  if (out_valid !== 1'b1 || correlation !== held_correlation || in_ready !== 1'b0) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"correlation\\\":\\\"0x%0h\\\",\\\"out_valid\\\":1,\\\"in_ready\\\":0}},\\\"actual\\\":{{\\\"correlation\\\":\\\"0x%0h\\\",\\\"out_valid\\\":\\\"%0b\\\",\\\"in_ready\\\":\\\"%0b\\\"}}}}",
                             oracle_scenario_id, oracle_scenario_class, oracle_item_index, held_correlation, correlation, out_valid, in_ready);
                    $display("TEST_FAIL correlation changed under backpressure");
                    $finish;
                  end
                end
                @(negedge clk);
                in_valid = 1'b0;
                out_ready = 1'b1;
                @(posedge clk);
                #1;
                if (out_valid !== 1'b0) begin
                  $display("TEST_FAIL out_valid did not clear");
                  $finish;
                end
              end
              $display("TEST_PASS");
              $finish;
            end else begin
              repeat (2) @(posedge clk);
              rst_n = 1'b1;

            // Template [-1, 2, -3, 4] responds to this reversed known pulse with 30.
            send_and_expect({width}'sd4, -{acc_width}'sd4);
            send_and_expect(-{width}'sd3, {acc_width}'sd11);
            send_and_expect({width}'sd2, -{acc_width}'sd20);
            send_and_expect(-{width}'sd1, {acc_width}'sd30);
            send_and_expect({width}'sd127, -{acc_width}'sd147);

            @(negedge clk);
            while (in_ready !== 1'b1) begin
              @(negedge clk);
            end
            out_ready = 1'b0;
            in_sample = -{width}'sd8;
            in_valid = 1'b1;
            @(posedge clk);
            #1;
            if (out_valid !== 1'b1 || correlation !== {acc_width}'sd273) begin
              $display("TEST_FAIL failed to capture stalled correlation");
              $finish;
            end
            held_correlation = correlation;
            @(negedge clk);
            in_valid = 1'b0;
            repeat (2) begin
              @(posedge clk);
              #1;
              if (out_valid !== 1'b1 || correlation !== held_correlation) begin
                $display("TEST_FAIL correlation changed under backpressure");
                $finish;
              end
            end
            @(negedge clk);
            out_ready = 1'b1;
            @(posedge clk);

            @(negedge clk);
            rst_n = 1'b0;
            repeat (2) @(posedge clk);
            @(negedge clk);
            rst_n = 1'b1;
            send_and_expect(-{width}'sd4, {acc_width}'sd4);

            $display("TEST_PASS");
            $finish;
            end
          end

          initial begin
            #8000;
            $display("TEST_FAIL timeout");
            $finish;
          end
        endmodule
        """
    )


def matched_filter_rtl_files(width: int) -> dict[str, str]:
    acc_width = width * 2 + 2
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [{width - 1}:0] in_sample,
            output wire out_valid,
            input wire out_ready,
            output wire signed [{acc_width - 1}:0] correlation
        );

          wire core_in_ready;
          wire ignored_last;
          assign in_ready = core_in_ready && !ignored_last;

          matched_filter_core #(
            .WIDTH({width}),
            .ACC_WIDTH({acc_width})
          ) u_matched_filter_core (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(core_in_ready),
            .in_sample(in_sample),
            .in_last(1'b0),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_correlation(correlation),
            .out_last(ignored_last)
          );

        endmodule
        """
    )
    core = dedent(
        f"""\
        module matched_filter_core #(
            parameter WIDTH = {width},
            parameter ACC_WIDTH = {acc_width},
            parameter TAP0 = -1,
            parameter TAP1 = 2,
            parameter TAP2 = -3,
            parameter TAP3 = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [WIDTH-1:0] in_sample,
            input wire in_last,
            output reg out_valid,
            input wire out_ready,
            output reg signed [ACC_WIDTH-1:0] out_correlation,
            output reg out_last
        );

          wire signed [ACC_WIDTH-1:0] in_sample_extended;
          wire signed [ACC_WIDTH-1:0] tap0_value;
          wire signed [ACC_WIDTH-1:0] tap1_value;
          wire signed [ACC_WIDTH-1:0] tap2_value;
          wire signed [ACC_WIDTH-1:0] tap3_value;
          reg signed [ACC_WIDTH-1:0] sample_d0;
          reg signed [ACC_WIDTH-1:0] sample_d1;
          reg signed [ACC_WIDTH-1:0] sample_d2;
          wire signed [ACC_WIDTH-1:0] sum0;
          wire signed [ACC_WIDTH-1:0] sum1;
          wire signed [ACC_WIDTH-1:0] sum2;
          wire signed [ACC_WIDTH-1:0] correlation_sum;

          assign in_sample_extended = {{{{(ACC_WIDTH-WIDTH){{in_sample[WIDTH-1]}}}}, in_sample}};
          assign tap0_value = TAP0;
          assign tap1_value = TAP1;
          assign tap2_value = TAP2;
          assign tap3_value = TAP3;
          assign in_ready = !out_valid || out_ready;

          matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap0 (.sample(in_sample_extended), .coefficient(tap0_value), .accum({{ACC_WIDTH{{1'b0}}}}), .result(sum0));
          matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap1 (.sample(sample_d0), .coefficient(tap1_value), .accum(sum0), .result(sum1));
          matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap2 (.sample(sample_d1), .coefficient(tap2_value), .accum(sum1), .result(sum2));
          matched_filter_mac #(.ACC_WIDTH(ACC_WIDTH)) u_tap3 (.sample(sample_d2), .coefficient(tap3_value), .accum(sum2), .result(correlation_sum));

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sample_d0 <= {{ACC_WIDTH{{1'b0}}}};
              sample_d1 <= {{ACC_WIDTH{{1'b0}}}};
              sample_d2 <= {{ACC_WIDTH{{1'b0}}}};
              out_valid <= 1'b0;
              out_correlation <= {{ACC_WIDTH{{1'b0}}}};
              out_last <= 1'b0;
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                out_correlation <= correlation_sum;
                out_last <= in_last;
                if (in_last) begin
                  sample_d0 <= {{ACC_WIDTH{{1'b0}}}};
                  sample_d1 <= {{ACC_WIDTH{{1'b0}}}};
                  sample_d2 <= {{ACC_WIDTH{{1'b0}}}};
                end else begin
                  sample_d2 <= sample_d1;
                  sample_d1 <= sample_d0;
                  sample_d0 <= in_sample_extended;
                end
              end
            end
          end
        endmodule
        """
    )
    mac = dedent(
        f"""\
        module matched_filter_mac #(
            parameter ACC_WIDTH = {acc_width}
        ) (
            input wire signed [ACC_WIDTH-1:0] sample,
            input wire signed [ACC_WIDTH-1:0] coefficient,
            input wire signed [ACC_WIDTH-1:0] accum,
            output wire signed [ACC_WIDTH-1:0] result
        );
          wire signed [ACC_WIDTH-1:0] product;
          assign product = $signed(sample) * $signed(coefficient);
          assign result = $signed(accum) + product;
        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/matched_filter_core.v": core,
        "rtl/matched_filter_mac.v": mac,
    }


def peak_detector_testbench(width: int) -> str:
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg signed [{width - 1}:0] in_sample;
          reg in_last;
          wire out_valid;
          reg out_ready;
          wire peak_found;
          wire signed [{width - 1}:0] peak_value;
          wire [{width - 1}:0] peak_index;
          reg held_found;
          reg signed [{width - 1}:0] held_value;
          reg [{width - 1}:0] held_index;
          localparam INPUT_RECORD_WIDTH = {width + 4};
          localparam EXPECTED_RECORD_WIDTH = {2 * width + 2};
          localparam MAX_ORACLE_TRANSACTIONS = 4096;
          reg [INPUT_RECORD_WIDTH-1:0] oracle_inputs [0:MAX_ORACLE_TRANSACTIONS-1];
          reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected [0:MAX_ORACLE_TRANSACTIONS-1];
          reg [INPUT_RECORD_WIDTH-1:0] oracle_input_record;
          reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected_record;
          reg oracle_expected_found;
          reg signed [{width - 1}:0] oracle_expected_value;
          reg [{width - 1}:0] oracle_expected_index;
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
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_sample(in_sample),
            .in_last(in_last),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .peak_found(peak_found),
            .peak_value(peak_value),
            .peak_index(peak_index)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_sample;
            input signed [{width - 1}:0] value;
            input last;
            begin
              @(negedge clk);
              while (in_ready !== 1'b1) begin
                @(negedge clk);
              end
              in_sample = value;
              in_last = last;
              in_valid = 1'b1;
              @(posedge clk);
              #1;
              @(negedge clk);
              in_valid = 1'b0;
              in_last = 1'b0;
            end
          endtask

          task expect_result;
            input expected_found;
            input signed [{width - 1}:0] expected_value;
            input [{width - 1}:0] expected_index;
            begin
              while (out_valid !== 1'b1) begin
                @(posedge clk);
                #1;
              end
              if (peak_found !== expected_found || peak_value !== expected_value || peak_index !== expected_index) begin
                $display("TEST_FAIL result expected found=%0d value=%0d index=%0d actual found=%0d value=%0d index=%0d", expected_found, expected_value, expected_index, peak_found, peak_value, peak_index);
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          task oracle_reset_dut;
            begin
              @(negedge clk);
              rst_n = 1'b0;
              in_valid = 1'b0;
              in_last = 1'b0;
              out_ready = 1'b1;
              repeat (2) @(posedge clk);
              @(negedge clk);
              rst_n = 1'b1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_sample = {width}'sd0;
            in_last = 1'b0;
            out_ready = 1'b1;
            held_found = 1'b0;
            held_value = {width}'sd0;
            held_index = {width}'d0;
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
              $readmemh(oracle_input_path, oracle_inputs, 0, oracle_transaction_count - 1);
              $readmemh(oracle_expected_path, oracle_expected, 0, oracle_transaction_count - 1);
              repeat (2) @(posedge clk);
              rst_n = 1'b1;
              for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count; oracle_item_index = oracle_item_index + 1) begin
                oracle_input_record = oracle_inputs[oracle_item_index];
                oracle_expected_record = oracle_expected[oracle_item_index];
                oracle_expected_value = oracle_expected_record[{width - 1}:0];
                oracle_expected_index = oracle_expected_record[{2 * width - 1}:{width}];
                oracle_expected_found = oracle_expected_record[{2 * width}];
                oracle_stall_cycles = oracle_input_record[{width + 3}:{width + 2}];
                if (oracle_input_record[{width + 1}]) begin
                  oracle_reset_dut;
                end
                @(negedge clk);
                while (in_ready !== 1'b1) begin
                  @(negedge clk);
                end
                out_ready = oracle_stall_cycles == 0;
                in_sample = oracle_input_record[{width - 1}:0];
                in_last = oracle_input_record[{width}];
                in_valid = 1'b1;
                @(posedge clk);
                #1;
                if (oracle_expected_record[{2 * width + 1}]) begin
                  if (out_valid !== 1'b1 || peak_found !== oracle_expected_found ||
                      peak_value !== oracle_expected_value || peak_index !== oracle_expected_index) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"found\\\":%0d,\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":%0d}},\\\"actual\\\":{{\\\"found\\\":\\\"%0b\\\",\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":\\\"0x%0h\\\",\\\"out_valid\\\":\\\"%0b\\\"}}}}",
                             oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                             oracle_expected_found, oracle_expected_value, oracle_expected_index,
                             peak_found, peak_value, peak_index, out_valid);
                    $display("TEST_FAIL functional mismatch");
                    $finish;
                  end
                  held_found = peak_found;
                  held_value = peak_value;
                  held_index = peak_index;
                end else if (out_valid !== 1'b0) begin
                  $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"out_valid\\\":0}},\\\"actual\\\":{{\\\"out_valid\\\":\\\"%0b\\\"}}}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index, out_valid);
                  $display("TEST_FAIL unexpected output");
                  $finish;
                end
                @(negedge clk);
                in_valid = 1'b0;
                in_last = 1'b0;
                if (oracle_expected_record[{2 * width + 1}]) begin
                  if (oracle_stall_cycles > 0) begin
                    in_sample = ~oracle_input_record[{width - 1}:0];
                    in_valid = 1'b1;
                    #1;
                    if (in_ready !== 1'b0) begin
                      $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"in_ready\\\":0}},\\\"actual\\\":{{\\\"in_ready\\\":\\\"%0b\\\"}}}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index, in_ready);
                      $display("TEST_FAIL accepted sample while result stalled");
                      $finish;
                    end
                  end
                  for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
                    @(posedge clk);
                    #1;
                    if (out_valid !== 1'b1 || peak_found !== held_found || peak_value !== held_value ||
                        peak_index !== held_index || in_ready !== 1'b0) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"found\\\":%0d,\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":%0d,\\\"in_ready\\\":0}},\\\"actual\\\":{{\\\"found\\\":\\\"%0b\\\",\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":\\\"0x%0h\\\",\\\"in_ready\\\":\\\"%0b\\\"}}}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                               held_found, held_value, held_index, peak_found, peak_value, peak_index, in_ready);
                      $display("TEST_FAIL result changed under backpressure");
                      $finish;
                    end
                  end
                  @(negedge clk);
                  in_valid = 1'b0;
                  out_ready = 1'b1;
                  @(posedge clk);
                  #1;
                  if (out_valid !== 1'b0) begin
                    $display("TEST_FAIL out_valid did not clear");
                    $finish;
                  end
                end
              end
              $display("TEST_PASS");
              $finish;
            end else begin
              repeat (2) @(posedge clk);
              rst_n = 1'b1;

            // A frame without a threshold-qualified sample produces the defined empty result.
            send_sample(-{width}'sd3, 1'b0);
            send_sample({width}'sd0, 1'b0);
            send_sample({width}'sd9, 1'b1);
            expect_result(1'b0, {width}'sd0, {width}'d0);

            // Equality at THRESHOLD qualifies, and a later larger sample wins.
            send_sample({width}'sd10, 1'b0);
            send_sample({width}'sd12, 1'b0);
            send_sample({width}'sd15, 1'b0);
            send_sample({width}'sd13, 1'b1);
            expect_result(1'b1, {width}'sd15, {width}'d2);

            // Equal maxima retain the first accepted index.
            send_sample({width}'sd11, 1'b0);
            send_sample({width}'sd16, 1'b0);
            send_sample({width}'sd16, 1'b0);
            send_sample({width}'sd14, 1'b1);
            expect_result(1'b1, {width}'sd16, {width}'d1);

            // The final accepted sample participates in the frame maximum.
            send_sample({width}'sd11, 1'b0);
            send_sample({width}'sd14, 1'b0);
            send_sample({width}'sd19, 1'b1);
            expect_result(1'b1, {width}'sd19, {width}'d2);

            // A completed output remains unchanged while downstream is stalled.
            @(negedge clk);
            out_ready = 1'b0;
            send_sample({width}'sd10, 1'b1);
            if (out_valid !== 1'b1 || peak_found !== 1'b1 || peak_value !== {width}'sd10 || peak_index !== {width}'d0) begin
              $display("TEST_FAIL stalled result was not captured");
              $finish;
            end
            held_found = peak_found;
            held_value = peak_value;
            held_index = peak_index;
            repeat (2) begin
              @(posedge clk);
              #1;
              if (out_valid !== 1'b1 || peak_found !== held_found || peak_value !== held_value || peak_index !== held_index) begin
                $display("TEST_FAIL result changed under backpressure");
                $finish;
              end
            end
            @(negedge clk);
            out_ready = 1'b1;
            @(posedge clk);

            // Reset discards partial-frame state and restarts indexing at zero.
            send_sample({width}'sd20, 1'b0);
            @(negedge clk);
            rst_n = 1'b0;
            repeat (2) @(posedge clk);
            @(negedge clk);
            rst_n = 1'b1;
            send_sample({width}'sd10, 1'b1);
            expect_result(1'b1, {width}'sd10, {width}'d0);

            $display("TEST_PASS");
            $finish;
            end
          end

          initial begin
            #2000;
            $display("TEST_FAIL timeout");
            $finish;
          end
        endmodule
        """
    )


def peak_detector_rtl_files(width: int) -> dict[str, str]:
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [{width - 1}:0] in_sample,
            input wire in_last,
            output wire out_valid,
            input wire out_ready,
            output wire peak_found,
            output wire signed [{width - 1}:0] peak_value,
            output wire [{width - 1}:0] peak_index
        );

          peak_detector_core #(
            .WIDTH({width}),
            .THRESHOLD(10)
          ) u_peak_detector_core (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_sample(in_sample),
            .in_last(in_last),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_peak_found(peak_found),
            .out_peak_value(peak_value),
            .out_peak_index(peak_index)
          );
        endmodule
        """
    )
    core = dedent(
        f"""\
        module peak_detector_core #(
            parameter WIDTH = {width},
            parameter THRESHOLD = 10
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [WIDTH-1:0] in_sample,
            input wire in_last,
            output reg out_valid,
            input wire out_ready,
            output reg out_peak_found,
            output reg signed [WIDTH-1:0] out_peak_value,
            output reg [WIDTH-1:0] out_peak_index
        );

          reg peak_found;
          reg signed [WIDTH-1:0] peak_value;
          reg [WIDTH-1:0] peak_index;
          reg [WIDTH-1:0] sample_index;
          wire sample_qualifies;
          wire signed [WIDTH-1:0] candidate_value;
          wire candidate_is_new_peak;
          wire candidate_found;
          wire [WIDTH-1:0] candidate_index;

          assign in_ready = !out_valid || out_ready;
          assign sample_qualifies = $signed(in_sample) >= THRESHOLD;
          assign candidate_value = in_sample;
          assign candidate_is_new_peak = sample_qualifies && (!peak_found || candidate_value > peak_value);
          assign candidate_found = peak_found || sample_qualifies;
          assign candidate_index = candidate_is_new_peak ? sample_index : peak_index;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              peak_found <= 1'b0;
              peak_value <= {{WIDTH{{1'b0}}}};
              peak_index <= {{WIDTH{{1'b0}}}};
              sample_index <= {{WIDTH{{1'b0}}}};
              out_valid <= 1'b0;
              out_peak_found <= 1'b0;
              out_peak_value <= {{WIDTH{{1'b0}}}};
              out_peak_index <= {{WIDTH{{1'b0}}}};
            end else if (in_ready) begin
              out_valid <= 1'b0;
              if (in_valid) begin
                if (in_last) begin
                  out_valid <= 1'b1;
                  out_peak_found <= candidate_found;
                  out_peak_value <= candidate_found ? (candidate_is_new_peak ? candidate_value : peak_value) : {{WIDTH{{1'b0}}}};
                  out_peak_index <= candidate_found ? candidate_index : {{WIDTH{{1'b0}}}};
                  peak_found <= 1'b0;
                  peak_value <= {{WIDTH{{1'b0}}}};
                  peak_index <= {{WIDTH{{1'b0}}}};
                  sample_index <= {{WIDTH{{1'b0}}}};
                end else begin
                  peak_found <= candidate_found;
                  if (candidate_is_new_peak) begin
                    peak_value <= candidate_value;
                    peak_index <= sample_index;
                  end
                  sample_index <= sample_index + 1'b1;
                end
              end
            end
          end
        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/peak_detector_core.v": core,
    }


def pulse_radar_signal_testbench(width: int) -> str:
    acc_width = width * 2 + 2
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg signed [{width - 1}:0] in_sample;
          reg in_last;
          wire out_valid;
          reg out_ready;
          wire peak_found;
          wire signed [{acc_width - 1}:0] peak_value;
          wire [{acc_width - 1}:0] peak_index;
          reg held_found;
          reg signed [{acc_width - 1}:0] held_value;
          reg [{acc_width - 1}:0] held_index;
          localparam INPUT_RECORD_WIDTH = {width + 4};
          localparam EXPECTED_RECORD_WIDTH = {2 * acc_width + 2};
          localparam MAX_ORACLE_TRANSACTIONS = 4096;
          reg [INPUT_RECORD_WIDTH-1:0] oracle_inputs [0:MAX_ORACLE_TRANSACTIONS-1];
          reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected [0:MAX_ORACLE_TRANSACTIONS-1];
          reg [INPUT_RECORD_WIDTH-1:0] oracle_input_record;
          reg [EXPECTED_RECORD_WIDTH-1:0] oracle_expected_record;
          reg oracle_expected_found;
          reg signed [{acc_width - 1}:0] oracle_expected_value;
          reg [{acc_width - 1}:0] oracle_expected_index;
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
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_sample(in_sample),
            .in_last(in_last),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .peak_found(peak_found),
            .peak_value(peak_value),
            .peak_index(peak_index)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_sample;
            input signed [{width - 1}:0] value;
            input last;
            begin
              @(negedge clk);
              while (in_ready !== 1'b1) begin
                @(negedge clk);
              end
              in_sample = value;
              in_last = last;
              in_valid = 1'b1;
              @(posedge clk);
              #1;
              @(negedge clk);
              in_valid = 1'b0;
              in_last = 1'b0;
            end
          endtask

          task expect_result;
            input expected_found;
            input signed [{acc_width - 1}:0] expected_value;
            input [{acc_width - 1}:0] expected_index;
            begin
              while (out_valid !== 1'b1) begin
                @(posedge clk);
                #1;
              end
              if (peak_found !== expected_found || peak_value !== expected_value || peak_index !== expected_index) begin
                $display("TEST_FAIL result expected found=%0d value=%0d index=%0d actual found=%0d value=%0d index=%0d", expected_found, expected_value, expected_index, peak_found, peak_value, peak_index);
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          task reset_dut;
            begin
              @(negedge clk);
              rst_n = 1'b0;
              repeat (2) @(posedge clk);
              @(negedge clk);
              rst_n = 1'b1;
            end
          endtask

          task send_known_pulse;
            input last_on_final;
            begin
              send_sample({width}'sd4, 1'b0);
              send_sample(-{width}'sd3, 1'b0);
              send_sample({width}'sd2, 1'b0);
              send_sample(-{width}'sd1, last_on_final);
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_sample = {width}'sd0;
            in_last = 1'b0;
            out_ready = 1'b1;
            held_found = 1'b0;
            held_value = {acc_width}'sd0;
            held_index = {acc_width}'d0;
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
              $readmemh(oracle_input_path, oracle_inputs, 0, oracle_transaction_count - 1);
              $readmemh(oracle_expected_path, oracle_expected, 0, oracle_transaction_count - 1);
              repeat (2) @(posedge clk);
              rst_n = 1'b1;
              for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count; oracle_item_index = oracle_item_index + 1) begin
                oracle_input_record = oracle_inputs[oracle_item_index];
                oracle_expected_record = oracle_expected[oracle_item_index];
                oracle_expected_value = oracle_expected_record[{acc_width - 1}:0];
                oracle_expected_index = oracle_expected_record[{2 * acc_width - 1}:{acc_width}];
                oracle_expected_found = oracle_expected_record[{2 * acc_width}];
                oracle_stall_cycles = oracle_input_record[{width + 3}:{width + 2}];
                if (oracle_input_record[{width + 1}]) begin
                  reset_dut;
                end
                @(negedge clk);
                while (in_ready !== 1'b1) begin
                  @(negedge clk);
                end
                out_ready = oracle_stall_cycles == 0;
                in_sample = oracle_input_record[{width - 1}:0];
                in_last = oracle_input_record[{width}];
                in_valid = 1'b1;
                @(posedge clk);
                #1;
                @(negedge clk);
                in_valid = 1'b0;
                in_last = 1'b0;
                if (oracle_expected_record[{2 * acc_width + 1}]) begin
                  while (out_valid !== 1'b1) begin
                    @(posedge clk);
                    #1;
                  end
                  if (peak_found !== oracle_expected_found || peak_value !== oracle_expected_value ||
                      peak_index !== oracle_expected_index) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"found\\\":%0d,\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":%0d}},\\\"actual\\\":{{\\\"found\\\":\\\"%0b\\\",\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":\\\"0x%0h\\\",\\\"out_valid\\\":\\\"%0b\\\"}}}}",
                             oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                             oracle_expected_found, oracle_expected_value, oracle_expected_index,
                             peak_found, peak_value, peak_index, out_valid);
                    $display("TEST_FAIL functional mismatch");
                    $finish;
                  end
                  held_found = peak_found;
                  held_value = peak_value;
                  held_index = peak_index;
                  @(negedge clk);
                end else if (out_valid === 1'b1) begin
                  $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"out_valid\\\":0}},\\\"actual\\\":{{\\\"out_valid\\\":\\\"1\\\"}}}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index);
                  $display("TEST_FAIL unexpected output");
                  $finish;
                end
                if (oracle_expected_record[{2 * acc_width + 1}]) begin
                  if (oracle_stall_cycles > 0) begin
                    in_sample = ~oracle_input_record[{width - 1}:0];
                    in_last = 1'b0;
                    in_valid = 1'b1;
                  end
                  for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
                    @(posedge clk);
                    #1;
                    if (out_valid !== 1'b1 || peak_found !== held_found || peak_value !== held_value ||
                        peak_index !== held_index || in_ready !== 1'b0) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{{\\\"found\\\":%0d,\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":%0d,\\\"in_ready\\\":0}},\\\"actual\\\":{{\\\"found\\\":\\\"%0b\\\",\\\"value\\\":\\\"0x%0h\\\",\\\"index\\\":\\\"0x%0h\\\",\\\"in_ready\\\":\\\"%0b\\\"}}}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                               held_found, held_value, held_index, peak_found, peak_value, peak_index, in_ready);
                      $display("TEST_FAIL result changed under backpressure");
                      $finish;
                    end
                  end
                  @(negedge clk);
                  in_valid = 1'b0;
                  in_last = 1'b0;
                  out_ready = 1'b1;
                  @(posedge clk);
                  #1;
                  if (out_valid !== 1'b0) begin
                    $display("TEST_FAIL out_valid did not clear");
                    $finish;
                  end
                end
              end
              $display("TEST_PASS");
              $finish;
            end else begin
              repeat (2) @(posedge clk);
              rst_n = 1'b1;

            // The known reversed pulse produces correlation 30 at the frame end.
            send_known_pulse(1'b1);
            expect_result(1'b1, {acc_width}'sd30, {acc_width}'d3);

            // Negative correlation and below threshold values clamp below 10 without a false peak.
            reset_dut;
            send_sample({width}'sd4, 1'b1);
            expect_result(1'b0, {acc_width}'sd0, {acc_width}'d0);

            // Equality at threshold qualifies; this also distinguishes the wrong-threshold mutant.
            reset_dut;
            send_sample(-{width}'sd10, 1'b1);
            expect_result(1'b1, {acc_width}'sd10, {acc_width}'d0);

            // Multiple equal peaks retain the first correlation index.
            reset_dut;
            send_known_pulse(1'b0);
            send_sample({width}'sd0, 1'b0);
            send_sample({width}'sd0, 1'b0);
            send_sample({width}'sd0, 1'b0);
            send_known_pulse(1'b1);
            expect_result(1'b1, {acc_width}'sd30, {acc_width}'d3);

            // The frame result and last marker remain coherent while the output is stalled.
            reset_dut;
            out_ready = 1'b0;
            send_known_pulse(1'b1);
            while (out_valid !== 1'b1) begin
              @(posedge clk);
              #1;
            end
            held_found = peak_found;
            held_value = peak_value;
            held_index = peak_index;
            send_sample(-{width}'sd10, 1'b1);
            repeat (2) begin
              @(posedge clk);
              #1;
              if (out_valid !== 1'b1 || peak_found !== held_found || peak_value !== held_value || peak_index !== held_index) begin
                $display("TEST_FAIL frame result changed under stall");
                $finish;
              end
            end
            @(negedge clk);
            out_ready = 1'b1;
            @(posedge clk);
            #1;
            expect_result(1'b1, {acc_width}'sd10, {acc_width}'d0);

            // Reset drops a partial matched-filter history before the next accepted frame end.
            send_sample({width}'sd4, 1'b0);
            send_sample(-{width}'sd3, 1'b0);
            reset_dut;
            send_sample(-{width}'sd10, 1'b1);
            expect_result(1'b1, {acc_width}'sd10, {acc_width}'d0);

            $display("TEST_PASS");
            $finish;
            end
          end

          initial begin
            #4000;
            $display("TEST_FAIL timeout");
            $finish;
          end
        endmodule
        """
    )


def pulse_radar_signal_rtl_files(width: int) -> dict[str, str]:
    acc_width = width * 2 + 2
    rtl_files = matched_filter_rtl_files(width)
    rtl_files.pop("rtl/top.v")
    rtl_files.update(peak_detector_rtl_files(acc_width))
    rtl_files.pop("rtl/top.v")
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [{width - 1}:0] in_sample,
            input wire in_last,
            output wire out_valid,
            input wire out_ready,
            output wire peak_found,
            output wire signed [{acc_width - 1}:0] peak_value,
            output wire [{acc_width - 1}:0] peak_index
        );

          wire correlation_valid;
          wire correlation_ready;
          wire signed [{acc_width - 1}:0] correlation;
          wire correlation_last;
          wire threshold_valid;
          wire threshold_ready;
          wire signed [{acc_width - 1}:0] thresholded_correlation;
          wire threshold_last;

          matched_filter_core #(
            .WIDTH({width}),
            .ACC_WIDTH({acc_width})
          ) u_matched_filter_core (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_sample(in_sample),
            .in_last(in_last),
            .out_valid(correlation_valid),
            .out_ready(correlation_ready),
            .out_correlation(correlation),
            .out_last(correlation_last)
          );

          threshold_comparator #(
            .ACC_WIDTH({acc_width}),
            .THRESHOLD(10)
          ) u_threshold_comparator (
            .in_valid(correlation_valid),
            .in_ready(correlation_ready),
            .in_sample(correlation),
            .in_last(correlation_last),
            .out_valid(threshold_valid),
            .out_ready(threshold_ready),
            .out_sample(thresholded_correlation),
            .out_last(threshold_last)
          );

          peak_detector_core #(
            .WIDTH({acc_width}),
            .THRESHOLD(10)
          ) u_peak_detector_core (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(threshold_valid),
            .in_ready(threshold_ready),
            .in_sample(thresholded_correlation),
            .in_last(threshold_last),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_peak_found(peak_found),
            .out_peak_value(peak_value),
            .out_peak_index(peak_index)
          );
        endmodule
        """
    )
    comparator = dedent(
        f"""\
        module threshold_comparator #(
            parameter ACC_WIDTH = {acc_width},
            parameter THRESHOLD = 10
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire signed [ACC_WIDTH-1:0] in_sample,
            input wire in_last,
            output wire out_valid,
            input wire out_ready,
            output wire signed [ACC_WIDTH-1:0] out_sample,
            output wire out_last
        );

          wire signed [ACC_WIDTH-1:0] threshold_value;
          wire signed [ACC_WIDTH-1:0] one_value;
          wire signed [ACC_WIDTH-1:0] clamp_value;

          // The bounded positive default threshold makes THRESHOLD - 1 a safe rejected value.
          assign threshold_value = THRESHOLD;
          assign one_value = {{{{(ACC_WIDTH-1){{1'b0}}}}, 1'b1}};
          assign clamp_value = $signed(threshold_value) - $signed(one_value);
          assign in_ready = out_ready;
          assign out_valid = in_valid;
          assign out_sample = $signed(in_sample) >= $signed(threshold_value) ? in_sample : clamp_value;
          assign out_last = in_last;
        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/matched_filter_core.v": rtl_files["rtl/matched_filter_core.v"],
        "rtl/matched_filter_mac.v": rtl_files["rtl/matched_filter_mac.v"],
        "rtl/threshold_comparator.v": comparator,
        "rtl/peak_detector_core.v": rtl_files["rtl/peak_detector_core.v"],
    }


def pwm_controller_testbench(width: int) -> str:
    msb = width - 1
    duty_value = 3 if width >= 3 else max(1, (1 << width) - 1)
    sample_cycles = 8 if width >= 3 else 1 << width
    expected_high = 3 if width >= 3 else duty_value
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg [{msb}:0] duty;
          wire pwm_out;
          integer high_count;
          integer i;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .duty(duty),
            .pwm_out(pwm_out)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            duty = {width}'d{duty_value};
            repeat (2) @(posedge clk);
            @(negedge clk);
            rst_n = 1'b1;

            high_count = 0;
            #1;
            if (pwm_out === 1'b1) begin
              high_count = high_count + 1;
            end
            for (i = 1; i < {sample_cycles}; i = i + 1) begin
              @(posedge clk);
              #1;
              if (pwm_out === 1'b1) begin
                high_count = high_count + 1;
              end
            end

            if (high_count != {expected_high}) begin
              $display("TEST_FAIL expected %0d high cycles got %0d", {expected_high}, high_count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def composed_vector_mac_pipeline_testbench(width: int) -> str:
    msb = width - 1
    score_width = width * 2
    score_msb = score_width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg feature_valid;
          wire feature_ready;
          reg [{msb}:0] feature_data;
          reg weight_valid;
          wire weight_ready;
          reg [{msb}:0] weight_data;
          reg [{score_msb}:0] bias;
          wire score_valid;
          reg score_ready;
          wire [{score_msb}:0] score_data;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .feature_valid(feature_valid),
            .feature_ready(feature_ready),
            .feature_data(feature_data),
            .weight_valid(weight_valid),
            .weight_ready(weight_ready),
            .weight_data(weight_data),
            .bias(bias),
            .score_valid(score_valid),
            .score_ready(score_ready),
            .score_data(score_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_pair;
            input [{msb}:0] feature;
            input [{msb}:0] weight;
            begin
              @(negedge clk);
              feature_valid = 1'b1;
              weight_valid = 1'b1;
              feature_data = feature;
              weight_data = weight;
              while (!(feature_ready && weight_ready)) begin
                @(negedge clk);
              end
              @(negedge clk);
              feature_valid = 1'b0;
              weight_valid = 1'b0;
              feature_data = {width}'d0;
              weight_data = {width}'d0;
            end
          endtask

          task expect_score;
            input [{score_msb}:0] expected;
            begin
              wait_cycles = 0;
              while (score_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (score_valid !== 1'b1) begin
                $display("TEST_FAIL score did not become valid");
                $finish;
              end
              if (score_data !== expected) begin
                $display("TEST_FAIL expected score=%0d got %0d", expected, score_data);
                $finish;
              end
              @(negedge clk);
            end
          endtask

          initial begin
            rst_n = 1'b0;
            feature_valid = 1'b0;
            feature_data = {width}'d0;
            weight_valid = 1'b0;
            weight_data = {width}'d0;
            bias = {score_width}'d0;
            score_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            bias = {score_width}'d3;
            send_pair({width}'d1, {width}'d2);
            send_pair({width}'d2, {width}'d3);
            send_pair({width}'d3, {width}'d4);
            send_pair({width}'d4, {width}'d5);
            expect_score({score_width}'d43);

            bias = {score_width}'d1;
            send_pair({width}'d2, {width}'d1);
            send_pair({width}'d1, {width}'d2);
            send_pair({width}'d0, {width}'d3);
            send_pair({width}'d3, {width}'d4);
            expect_score({score_width}'d17);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def pwm_controller_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] duty,
            output wire pwm_out
        );

          wire [{msb}:0] counter;

          pwm_timer #(
            .WIDTH({width})
          ) u_pwm_timer (
            .clk(clk),
            .rst_n(rst_n),
            .counter(counter)
          );

          pwm_channel #(
            .WIDTH({width})
          ) u_pwm_channel (
            .counter(counter),
            .duty(duty),
            .pwm_out(pwm_out)
          );

        endmodule
        """
    )
    pwm_timer = dedent(
        """\
        module pwm_timer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            output reg [WIDTH-1:0] counter
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              counter <= {WIDTH{1'b0}};
            end else begin
              counter <= counter + {{(WIDTH-1){1'b0}}, 1'b1};
            end
          end

        endmodule
        """
    )
    pwm_channel = dedent(
        """\
        module pwm_channel #(
            parameter WIDTH = 8
        ) (
            input wire [WIDTH-1:0] counter,
            input wire [WIDTH-1:0] duty,
            output wire pwm_out
        );

          assign pwm_out = (counter < duty);

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/pwm_timer.v": pwm_timer,
        "rtl/pwm_channel.v": pwm_channel,
    }


def composed_vector_mac_pipeline_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    score_width = width * 2
    score_msb = score_width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire feature_valid,
            output wire feature_ready,
            input wire [{msb}:0] feature_data,
            input wire weight_valid,
            output wire weight_ready,
            input wire [{msb}:0] weight_data,
            input wire [{score_msb}:0] bias,
            output wire score_valid,
            input wire score_ready,
            output wire [{score_msb}:0] score_data
        );

          wire feature_buf_valid;
          wire feature_buf_ready;
          wire [{msb}:0] feature_buf_data;
          wire weight_buf_valid;
          wire weight_buf_ready;
          wire [{msb}:0] weight_buf_data;
          wire mac_score_valid;
          wire mac_score_ready;
          wire [{score_msb}:0] mac_score_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_feature_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(feature_valid),
            .in_ready(feature_ready),
            .in_data(feature_data),
            .out_valid(feature_buf_valid),
            .out_ready(feature_buf_ready),
            .out_data(feature_buf_data)
          );

          skid_buffer #(
            .WIDTH({width})
          ) u_weight_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(weight_valid),
            .in_ready(weight_ready),
            .in_data(weight_data),
            .out_valid(weight_buf_valid),
            .out_ready(weight_buf_ready),
            .out_data(weight_buf_data)
          );

          vector_mac_core #(
            .DATA_WIDTH({width}),
            .SCORE_WIDTH({score_width})
          ) u_vector_mac_core (
            .clk(clk),
            .rst_n(rst_n),
            .feature_valid(feature_buf_valid),
            .feature_ready(feature_buf_ready),
            .feature_data(feature_buf_data),
            .weight_valid(weight_buf_valid),
            .weight_ready(weight_buf_ready),
            .weight_data(weight_buf_data),
            .bias(bias),
            .score_valid(mac_score_valid),
            .score_ready(mac_score_ready),
            .score_data(mac_score_data)
          );

          stream_stage #(
            .WIDTH({score_width})
          ) u_score_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(mac_score_valid),
            .in_ready(mac_score_ready),
            .in_data(mac_score_data),
            .out_valid(score_valid),
            .out_ready(score_ready),
            .out_data(score_data)
          );

        endmodule
        """
    )
    skid_buffer = dedent(
        """\
        module skid_buffer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          reg valid_r;
          reg [WIDTH-1:0] data_r;

          assign in_ready = !valid_r || out_ready;
          assign out_valid = valid_r;
          assign out_data = data_r;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_r <= 1'b0;
              data_r <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              valid_r <= in_valid;
              if (in_valid) begin
                data_r <= in_data;
              end
            end
          end

        endmodule
        """
    )
    vector_mac_core = dedent(
        """\
        module vector_mac_core #(
            parameter DATA_WIDTH = 8,
            parameter SCORE_WIDTH = 16
        ) (
            input wire clk,
            input wire rst_n,
            input wire feature_valid,
            output wire feature_ready,
            input wire [DATA_WIDTH-1:0] feature_data,
            input wire weight_valid,
            output wire weight_ready,
            input wire [DATA_WIDTH-1:0] weight_data,
            input wire [SCORE_WIDTH-1:0] bias,
            output reg score_valid,
            input wire score_ready,
            output reg [SCORE_WIDTH-1:0] score_data
        );

          reg [SCORE_WIDTH-1:0] accumulator;
          reg [1:0] vector_index;
          localparam [1:0] LAST_INDEX = 2'd3;
          wire accept_pair;
          wire [SCORE_WIDTH-1:0] product;
          wire [SCORE_WIDTH-1:0] next_accumulator;

          assign feature_ready = weight_valid && !score_valid;
          assign weight_ready = feature_valid && !score_valid;
          assign accept_pair = feature_valid && feature_ready && weight_valid && weight_ready;
          assign product = feature_data * weight_data;
          assign next_accumulator = accumulator + product;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              accumulator <= {SCORE_WIDTH{1'b0}};
              vector_index <= 2'd0;
              score_valid <= 1'b0;
              score_data <= {SCORE_WIDTH{1'b0}};
            end else begin
              if (score_valid && score_ready) begin
                score_valid <= 1'b0;
              end
              if (accept_pair) begin
                if (vector_index == LAST_INDEX) begin
                  score_data <= next_accumulator + bias;
                  score_valid <= 1'b1;
                  accumulator <= {SCORE_WIDTH{1'b0}};
                  vector_index <= 2'd0;
                end else begin
                  accumulator <= next_accumulator;
                  vector_index <= vector_index + 2'd1;
                end
              end
            end
          end

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output reg out_valid,
            input wire out_ready,
            output reg [WIDTH-1:0] out_data
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              out_data <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                out_data <= in_data;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/vector_mac_core.v": vector_mac_core,
        "rtl/stream_stage.v": stream_stage,
    }


def fir_filter_testbench(width: int) -> str:
    msb = width - 1
    result_msb = width + 2
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg sample_valid;
          wire sample_ready;
          reg signed [{msb}:0] sample;
          wire result_valid;
          reg result_ready;
          wire signed [{result_msb}:0] result;
          localparam RESULT_WIDTH = {width + 3};
          localparam INPUT_RECORD_WIDTH = {width + 3};
          localparam EXPECTED_RECORD_WIDTH = {width + 4};
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

          task send_and_expect;
            input signed [{msb}:0] value;
            input signed [{result_msb}:0] expected;
            begin
              @(negedge clk);
              while (sample_ready !== 1'b1) begin
                @(negedge clk);
              end
              sample = value;
              sample_valid = 1'b1;
              @(posedge clk);
              #1;
              if (result_valid !== 1'b1) begin
                $display("TEST_FAIL result_valid was not asserted");
                $finish;
              end
              if (result !== expected) begin
                $display("TEST_FAIL expected result=%0d got %0d", expected, result);
                $finish;
              end
              @(negedge clk);
              sample_valid = 1'b0;
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
            result_ready = 1'b1;
            sample = {width}'sd0;
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
                oracle_stall_cycles = oracle_input_record[{width + 2}:{width + 1}];
                if (oracle_input_record[{width}]) begin
                  oracle_reset_dut;
                end
                @(negedge clk);
                while (sample_ready !== 1'b1) begin
                  @(negedge clk);
                end
                result_ready = oracle_stall_cycles == 0;
                sample = oracle_input_record[{width - 1}:0];
                sample_valid = 1'b1;
                @(posedge clk);
                #1;
                if (!oracle_expected_record[RESULT_WIDTH] || result_valid !== 1'b1 || result !== oracle_expected_result) begin
                  $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":\\\"0x%0h\\\",\\\"actual\\\":\\\"0x%0h\\\"}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index, oracle_expected_result, result);
                  $display("TEST_FAIL functional mismatch");
                  $finish;
                end
                oracle_held_result = result;
                @(negedge clk);
                sample_valid = 1'b0;
                for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
                  @(posedge clk);
                  #1;
                  if (result_valid !== 1'b1 || result !== oracle_held_result) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":\\\"0x%0h\\\",\\\"actual\\\":\\\"0x%0h\\\"}}",
                             oracle_scenario_id, oracle_scenario_class, oracle_item_index, oracle_held_result, result);
                    $display("TEST_FAIL result changed under backpressure");
                    $finish;
                  end
                end
                @(negedge clk);
                result_ready = 1'b1;
                @(posedge clk);
                #1;
                if (result_valid !== 1'b0) begin
                  $display("TEST_FAIL result_valid did not clear");
                  $finish;
                end
              end
              $display("TEST_PASS");
              $finish;
            end else begin
              repeat (2) @(posedge clk);
              rst_n = 1'b1;

              send_and_expect({width}'sd5, {width + 3}'sd15);
              send_and_expect(-{width}'sd4, -{width + 3}'sd22);
              send_and_expect({width}'sd7, {width + 3}'sd34);

              @(negedge clk);
              rst_n = 1'b0;
              repeat (2) @(posedge clk);
              @(negedge clk);
              rst_n = 1'b1;
              send_and_expect({width}'sd127, {width + 3}'sd381);

              @(posedge clk);
              #1;
              @(negedge clk);
              while (sample_ready !== 1'b1) begin
                @(negedge clk);
              end
              result_ready = 1'b0;
              sample = {width}'sd9;
              sample_valid = 1'b1;
              @(posedge clk);
              #1;
              if (result_valid !== 1'b1 || result !== -{width + 3}'sd227) begin
                $display("TEST_FAIL failed to capture result before backpressure");
                $finish;
              end
              @(negedge clk);
              sample = -{width}'sd11;
              repeat (2) begin
                @(posedge clk);
                #1;
                if (result_valid !== 1'b1 || result !== -{width + 3}'sd227) begin
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
              $display("TEST_PASS");
              $finish;
            end
          end
        endmodule
        """
    )


def matrix_vector_mac_testbench(width: int) -> str:
    result_msb = width + 3
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg sample_valid;
          wire sample_ready;
          reg signed [{width - 1}:0] sample;
          wire result_valid;
          reg result_ready;
          wire signed [{result_msb}:0] result;
          localparam RESULT_WIDTH = {width + 4};
          localparam INPUT_RECORD_WIDTH = {width + 3};
          localparam EXPECTED_RECORD_WIDTH = {width + 5};
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
            input signed [{width - 1}:0] value;
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
            input signed [{width - 1}:0] value0;
            input signed [{width - 1}:0] value1;
            input signed [{width - 1}:0] value2;
            input signed [{width - 1}:0] value3;
            input signed [{result_msb}:0] expected;
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
            sample = {width}'sd0;
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
                oracle_stall_cycles = oracle_input_record[{width + 2}:{width + 1}];
                if (oracle_input_record[{width}]) begin
                  oracle_reset_dut;
                end
                @(negedge clk);
                while (sample_ready !== 1'b1) begin
                  @(negedge clk);
                end
                result_ready = oracle_stall_cycles == 0;
                sample = oracle_input_record[{width - 1}:0];
                sample_valid = 1'b1;
                @(posedge clk);
                #1;
                if (oracle_expected_record[RESULT_WIDTH]) begin
                  if (result_valid !== 1'b1 || result !== oracle_expected_result) begin
                    $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":\\\"0x%0h\\\",\\\"actual\\\":\\\"0x%0h\\\"}}",
                             oracle_scenario_id, oracle_scenario_class, oracle_item_index, oracle_expected_result, result);
                    $display("TEST_FAIL functional mismatch");
                    $finish;
                  end
                  oracle_held_result = result;
                end else if (result_valid !== 1'b0) begin
                  $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":\\\"no_output\\\",\\\"actual\\\":\\\"0x%0h\\\"}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index, result);
                  $display("TEST_FAIL unexpected output");
                  $finish;
                end
                @(negedge clk);
                sample_valid = 1'b0;
                if (oracle_expected_record[RESULT_WIDTH]) begin
                  if (oracle_stall_cycles > 0) begin
                    sample = ~oracle_input_record[{width - 1}:0];
                    sample_valid = 1'b1;
                    #1;
                    if (sample_ready !== 1'b0) begin
                      $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":\\\"ready=0\\\",\\\"actual\\\":\\\"ready=%0b\\\"}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index, sample_ready);
                      $display("TEST_FAIL accepted sample while result stalled");
                      $finish;
                    end
                  end
                  for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles; oracle_stall_index = oracle_stall_index + 1) begin
                    @(posedge clk);
                    #1;
                    if (result_valid !== 1'b1 || result !== oracle_held_result) begin
                      $display("SR2FPGA_MISMATCH {{\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":\\\"0x%0h\\\",\\\"actual\\\":\\\"0x%0h\\\"}}",
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
                {width}'sd1, {width}'sd2, {width}'sd3, {width}'sd4, {width + 4}'sd13
              );
              send_vector_and_expect(
                {width}'sd127, -{width}'sd128, {width}'sd127, {width}'sd127, {width + 4}'sd890
              );

              @(negedge clk);
              rst_n = 1'b0;
              repeat (2) @(posedge clk);
              @(negedge clk);
              rst_n = 1'b1;
              send_sample({width}'sd5);
              send_sample({width}'sd6);
              send_sample({width}'sd7);
              @(negedge clk);
              result_ready = 1'b0;
              send_sample({width}'sd8);
              if (result_valid !== 1'b1 || result !== {width + 4}'sd33) begin
                $display("TEST_FAIL failed to capture stalled result");
                $finish;
              end
              sample = {width}'sd9;
              sample_valid = 1'b1;
              #1;
              if (sample_ready !== 1'b0) begin
                $display("TEST_FAIL accepted sample while result stalled");
                $finish;
              end
              repeat (2) begin
                @(posedge clk);
                #1;
                if (result_valid !== 1'b1 || result !== {width + 4}'sd33) begin
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
        endmodule
        """
    )


def fir_filter_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    result_msb = width + 2
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            output wire sample_ready,
            input wire signed [{msb}:0] sample,
            output wire result_valid,
            input wire result_ready,
            output wire signed [{result_msb}:0] result
        );

          // fir_filter_core contains the mac_unit tap helpers.
          fir_filter_core #(
            .WIDTH({width}),
            .RESULT_WIDTH({width + 3})
          ) u_fir_filter_core (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample(sample),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .result(result)
          );

        endmodule
        """
    )
    fir_filter_core = dedent(
        """\
        module fir_filter_core #(
            parameter WIDTH = 8,
            parameter RESULT_WIDTH = 11
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            output wire sample_ready,
            input wire signed [WIDTH-1:0] sample,
            output reg result_valid,
            input wire result_ready,
            output reg signed [RESULT_WIDTH-1:0] result
        );

          localparam signed [2:0] COEFF_NEW = 3'sd3;
          localparam signed [2:0] COEFF_PREV = -3'sd2;
          localparam signed [2:0] COEFF_OLD = 3'sd1;

          reg signed [WIDTH-1:0] sample_d0;
          reg signed [WIDTH-1:0] sample_d1;
          wire signed [RESULT_WIDTH-1:0] stage0;
          wire signed [RESULT_WIDTH-1:0] stage1;
          wire signed [RESULT_WIDTH-1:0] filtered_result;

          assign sample_ready = !result_valid || result_ready;

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_new_sample (
            .sample(sample),
            .coefficient(COEFF_NEW),
            .accum({RESULT_WIDTH{1'b0}}),
            .result(stage0)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_previous_sample (
            .sample(sample_d0),
            .coefficient(COEFF_PREV),
            .accum(stage0),
            .result(stage1)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_oldest_sample (
            .sample(sample_d1),
            .coefficient(COEFF_OLD),
            .accum(stage1),
            .result(filtered_result)
          );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sample_d0 <= {WIDTH{1'b0}};
              sample_d1 <= {WIDTH{1'b0}};
              result_valid <= 1'b0;
              result <= {RESULT_WIDTH{1'b0}};
            end else if (sample_ready) begin
              result_valid <= sample_valid;
              if (sample_valid) begin
                result <= filtered_result;
                sample_d1 <= sample_d0;
                sample_d0 <= sample;
              end
            end
          end

        endmodule
        """
    )
    mac_unit = dedent(
        """\
        module mac_unit #(
            parameter WIDTH = 8,
            parameter ACC_WIDTH = 11
        ) (
            input wire [WIDTH-1:0] sample,
            input wire [2:0] coefficient,
            input wire signed [ACC_WIDTH-1:0] accum,
            output wire signed [ACC_WIDTH-1:0] result
        );

          wire signed [ACC_WIDTH-1:0] product;

          assign product = $signed(sample) * $signed(coefficient);
          assign result = $signed(accum) + product;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/fir_filter_core.v": fir_filter_core,
        "rtl/mac_unit.v": mac_unit,
    }


def matrix_vector_mac_rtl_files(width: int) -> dict[str, str]:
    result_msb = width + 3
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            output wire sample_ready,
            input wire signed [{width - 1}:0] sample,
            output wire result_valid,
            input wire result_ready,
            output wire signed [{result_msb}:0] result
        );

          // dot_product_engine contains mac_unit and vector_rom instances.
          dot_product_engine #(
            .WIDTH({width}),
            .RESULT_WIDTH({width + 4})
          ) u_dot_product_engine (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample(sample),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .result(result)
          );

        endmodule
        """
    )
    dot_product_engine = dedent(
        """\
        module dot_product_engine #(
            parameter WIDTH = 8,
            parameter RESULT_WIDTH = 12
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            output wire sample_ready,
            input wire signed [WIDTH-1:0] sample,
            output reg result_valid,
            input wire result_ready,
            output reg signed [RESULT_WIDTH-1:0] result
        );

          reg [1:0] index;
          reg signed [RESULT_WIDTH-1:0] accum;
          wire signed [2:0] coefficient;
          wire signed [RESULT_WIDTH-1:0] next_accum;

          assign sample_ready = !result_valid || result_ready;

          vector_rom u_vector_rom (
            .addr(index),
            .coefficient(coefficient)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_unit (
            .sample(sample),
            .coefficient(coefficient),
            .accum(accum),
            .result(next_accum)
          );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              index <= 2'd0;
              accum <= {RESULT_WIDTH{1'b0}};
              result_valid <= 1'b0;
              result <= {RESULT_WIDTH{1'b0}};
            end else begin
              if (result_valid && result_ready) begin
                result_valid <= 1'b0;
              end
              if (sample_valid && sample_ready) begin
                if (index == 2'd3) begin
                  result <= next_accum;
                  result_valid <= 1'b1;
                  index <= 2'd0;
                  accum <= {RESULT_WIDTH{1'b0}};
                end else begin
                  accum <= next_accum;
                  index <= index + 2'd1;
                end
              end
            end
          end

        endmodule
        """
    )
    mac_unit = dedent(
        """\
        module mac_unit #(
            parameter WIDTH = 8,
            parameter ACC_WIDTH = 12
        ) (
            input wire [WIDTH-1:0] sample,
            input wire [2:0] coefficient,
            input wire signed [ACC_WIDTH-1:0] accum,
            output wire signed [ACC_WIDTH-1:0] result
        );

          wire signed [ACC_WIDTH-1:0] product;

          assign product = $signed(sample) * $signed(coefficient);
          assign result = $signed(accum) + product;

        endmodule
        """
    )
    vector_rom = dedent(
        """\
        module vector_rom (
            input wire [1:0] addr,
            output reg signed [2:0] coefficient
        );

          always @* begin
            case (addr)
              2'd0: coefficient = 3'sd2;
              2'd1: coefficient = -3'sd1;
              2'd2: coefficient = 3'sd3;
              default: coefficient = 3'sd1;
            endcase
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/dot_product_engine.v": dot_product_engine,
        "rtl/mac_unit.v": mac_unit,
        "rtl/vector_rom.v": vector_rom,
    }


def alu_control_unit_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg valid;
          wire ready;
          reg [2:0] op;
          reg [{msb}:0] lhs;
          reg [{msb}:0] rhs;
          wire result_valid;
          wire [{msb}:0] result;
          wire zero;
          wire carry;
          wire negative;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .valid(valid),
            .ready(ready),
            .op(op),
            .lhs(lhs),
            .rhs(rhs),
            .result_valid(result_valid),
            .result(result),
            .zero(zero),
            .carry(carry),
            .negative(negative)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task expect_result;
            input [2:0] op_i;
            input [{msb}:0] lhs_i;
            input [{msb}:0] rhs_i;
            input [{msb}:0] expected_result;
            input expected_zero;
            input expected_carry;
            input expected_negative;
            begin
              @(negedge clk);
              valid = 1'b1;
              op = op_i;
              lhs = lhs_i;
              rhs = rhs_i;
              @(negedge clk);
              valid = 1'b0;
              if (ready !== 1'b1) begin
                $display("TEST_FAIL ready was not asserted");
                $finish;
              end
              if (result_valid !== 1'b1) begin
                $display("TEST_FAIL result_valid was not asserted for op=%0d", op_i);
                $finish;
              end
              if (result !== expected_result) begin
                $display(
                  "TEST_FAIL op=%0d expected result=%0h got %0h",
                  op_i,
                  expected_result,
                  result
                );
                $finish;
              end
              if (zero !== expected_zero || carry !== expected_carry || negative !== expected_negative) begin
                $display("TEST_FAIL flags op=%0d zero=%0b carry=%0b negative=%0b", op_i, zero, carry, negative);
                $finish;
              end
            end
          endtask

          initial begin
            rst_n = 1'b0;
            valid = 1'b0;
            op = 3'd0;
            lhs = {width}'d0;
            rhs = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            expect_result(3'b000, 8'hff, 8'h01, 8'h00, 1'b1, 1'b1, 1'b0);
            expect_result(3'b001, 8'h03, 8'h01, 8'h02, 1'b0, 1'b0, 1'b0);
            expect_result(3'b010, 8'haa, 8'h0f, 8'h0a, 1'b0, 1'b0, 1'b0);
            expect_result(3'b011, 8'ha0, 8'h0f, 8'haf, 1'b0, 1'b0, 1'b1);
            expect_result(3'b100, 8'hff, 8'h0f, 8'hf0, 1'b0, 1'b0, 1'b1);
            expect_result(3'b101, 8'h11, 8'h01, 8'h22, 1'b0, 1'b0, 1'b0);
            expect_result(3'b110, 8'h80, 8'h02, 8'h20, 1'b0, 1'b0, 1'b0);
            expect_result(3'b111, 8'h5a, 8'h00, 8'h5a, 1'b0, 1'b0, 1'b0);

            @(posedge clk);
            #1;
            if (result_valid !== 1'b0) begin
              $display("TEST_FAIL result_valid did not clear");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def crc_stream_checker_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          reg frame_start;
          reg frame_end;
          reg [7:0] expected_crc;
          wire out_valid;
          reg out_ready;
          wire [7:0] crc_value;
          wire crc_match;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .frame_start(frame_start),
            .frame_end(frame_end),
            .expected_crc(expected_crc),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .crc_value(crc_value),
            .crc_match(crc_match)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_byte;
            input [7:0] value;
            input start_i;
            input end_i;
            begin
              @(negedge clk);
              in_valid = 1'b1;
              in_data = value;
              frame_start = start_i;
              frame_end = end_i;
              @(negedge clk);
              if (in_ready !== 1'b1) begin
                $display("TEST_FAIL input was not ready");
                $finish;
              end
              in_valid = 1'b0;
              in_data = {width}'d0;
              frame_start = 1'b0;
              frame_end = 1'b0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            frame_start = 1'b0;
            frame_end = 1'b0;
            expected_crc = 8'h7c;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_byte(8'h12, 1'b1, 1'b0);
            send_byte(8'h34, 1'b0, 1'b0);
            send_byte(8'h56, 1'b0, 1'b1);

            @(posedge clk);
            #1;
            if (out_valid !== 1'b1) begin
              $display("TEST_FAIL out_valid was not asserted");
              $finish;
            end
            if (crc_value !== 8'h7c) begin
              $display("TEST_FAIL expected crc=7c got %0h", crc_value);
              $finish;
            end
            if (crc_match !== 1'b1) begin
              $display("TEST_FAIL crc_match was not asserted");
              $finish;
            end
            @(posedge clk);
            #1;
            if (out_valid !== 1'b0) begin
              $display("TEST_FAIL out_valid did not clear after ready");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def alu_control_unit_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    shift_msb = min(2, width - 1)
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire valid,
            output wire ready,
            input wire [2:0] op,
            input wire [{msb}:0] lhs,
            input wire [{msb}:0] rhs,
            output wire result_valid,
            output wire [{msb}:0] result,
            output wire zero,
            output wire carry,
            output wire negative
        );

          wire [2:0] decoded_op;
          wire [{msb}:0] alu_result;
          wire alu_carry;

          assign ready = 1'b1;

          control_decode u_control_decode (
            .op(op),
            .decoded_op(decoded_op)
          );

          alu_core #(
            .WIDTH({width})
          ) u_alu_core (
            .op(decoded_op),
            .lhs(lhs),
            .rhs(rhs),
            .result(alu_result),
            .carry(alu_carry)
          );

          status_flags #(
            .WIDTH({width})
          ) u_status_flags (
            .clk(clk),
            .rst_n(rst_n),
            .valid(valid),
            .alu_result(alu_result),
            .alu_carry(alu_carry),
            .result_valid(result_valid),
            .result(result),
            .zero(zero),
            .carry(carry),
            .negative(negative)
          );

        endmodule
        """
    )
    control_decode = dedent(
        """\
        module control_decode (
            input wire [2:0] op,
            output wire [2:0] decoded_op
        );

          assign decoded_op = op;

        endmodule
        """
    )
    alu_core = dedent(
        f"""\
        module alu_core #(
            parameter WIDTH = 8
        ) (
            input wire [2:0] op,
            input wire [WIDTH-1:0] lhs,
            input wire [WIDTH-1:0] rhs,
            output reg [WIDTH-1:0] result,
            output reg carry
        );

          wire [WIDTH:0] add_ext;
          wire [WIDTH:0] sub_ext;

          assign add_ext = {{1'b0, lhs}} + {{1'b0, rhs}};
          assign sub_ext = {{1'b0, lhs}} - {{1'b0, rhs}};

          always @* begin
            result = {{WIDTH{{1'b0}}}};
            carry = 1'b0;
            case (op)
              3'b000: begin
                result = add_ext[WIDTH-1:0];
                carry = add_ext[WIDTH];
              end
              3'b001: begin
                result = sub_ext[WIDTH-1:0];
                carry = sub_ext[WIDTH];
              end
              3'b010: result = lhs & rhs;
              3'b011: result = lhs | rhs;
              3'b100: result = lhs ^ rhs;
              3'b101: result = lhs << rhs[{shift_msb}:0];
              3'b110: result = lhs >> rhs[{shift_msb}:0];
              default: result = lhs;
            endcase
          end

        endmodule
        """
    )
    status_flags = dedent(
        """\
        module status_flags #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire valid,
            input wire [WIDTH-1:0] alu_result,
            input wire alu_carry,
            output reg result_valid,
            output reg [WIDTH-1:0] result,
            output reg zero,
            output reg carry,
            output reg negative
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              result_valid <= 1'b0;
              result <= {WIDTH{1'b0}};
              zero <= 1'b0;
              carry <= 1'b0;
              negative <= 1'b0;
            end else if (valid) begin
              result_valid <= 1'b1;
              result <= alu_result;
              zero <= (alu_result == {WIDTH{1'b0}});
              carry <= alu_carry;
              negative <= alu_result[WIDTH-1];
            end else begin
              result_valid <= 1'b0;
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/control_decode.v": control_decode,
        "rtl/alu_core.v": alu_core,
        "rtl/status_flags.v": status_flags,
    }


def crc_stream_checker_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            input wire frame_start,
            input wire frame_end,
            input wire [7:0] expected_crc,
            output wire out_valid,
            input wire out_ready,
            output wire [7:0] crc_value,
            output wire crc_match
        );

          wire [7:0] crc_state;
          wire [7:0] crc_base;
          wire [7:0] crc_next;
          wire [7:0] frame_crc;
          wire frame_done;

          assign crc_base = frame_start ? 8'h00 : crc_state;

          crc8_update u_crc8_update (
            .crc_in(crc_base),
            .data_in(in_data[7:0]),
            .crc_out(crc_next)
          );

          stream_frame_accumulator u_stream_frame_accumulator (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .frame_end(frame_end),
            .out_ready(out_ready),
            .crc_next(crc_next),
            .crc_state(crc_state),
            .frame_done(frame_done),
            .frame_crc(frame_crc)
          );

          crc_status u_crc_status (
            .clk(clk),
            .rst_n(rst_n),
            .frame_done(frame_done),
            .out_ready(out_ready),
            .frame_crc(frame_crc),
            .expected_crc(expected_crc),
            .out_valid(out_valid),
            .crc_value(crc_value),
            .crc_match(crc_match)
          );

        endmodule
        """
    )
    crc8_update = dedent(
        """\
        module crc8_update (
            input wire [7:0] crc_in,
            input wire [7:0] data_in,
            output reg [7:0] crc_out
        );

          integer bit_index;
          reg [7:0] crc_work;

          always @* begin
            crc_work = crc_in ^ data_in;
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
              if (crc_work[7]) begin
                crc_work = (crc_work << 1) ^ 8'h07;
              end else begin
                crc_work = crc_work << 1;
              end
            end
            crc_out = crc_work;
          end

        endmodule
        """
    )
    stream_frame_accumulator = dedent(
        """\
        module stream_frame_accumulator (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire frame_end,
            input wire out_ready,
            input wire [7:0] crc_next,
            output reg [7:0] crc_state,
            output reg frame_done,
            output reg [7:0] frame_crc
        );

          wire accept;

          assign in_ready = !frame_done || out_ready;
          assign accept = in_valid && in_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              crc_state <= 8'h00;
              frame_done <= 1'b0;
              frame_crc <= 8'h00;
            end else begin
              if (frame_done && out_ready) begin
                frame_done <= 1'b0;
              end
              if (accept) begin
                crc_state <= crc_next;
                if (frame_end) begin
                  frame_done <= 1'b1;
                  frame_crc <= crc_next;
                end
              end
            end
          end

        endmodule
        """
    )
    crc_status = dedent(
        """\
        module crc_status (
            input wire clk,
            input wire rst_n,
            input wire frame_done,
            input wire out_ready,
            input wire [7:0] frame_crc,
            input wire [7:0] expected_crc,
            output reg out_valid,
            output reg [7:0] crc_value,
            output reg crc_match
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              crc_value <= 8'h00;
              crc_match <= 1'b0;
            end else if (frame_done) begin
              out_valid <= 1'b1;
              crc_value <= frame_crc;
              crc_match <= (frame_crc == expected_crc);
            end else if (out_valid && out_ready) begin
              out_valid <= 1'b0;
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/crc8_update.v": crc8_update,
        "rtl/stream_frame_accumulator.v": stream_frame_accumulator,
        "rtl/crc_status.v": crc_status,
    }
