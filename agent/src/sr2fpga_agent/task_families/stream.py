"""Stable family metadata for stream and composed generator tasks."""

from textwrap import dedent

TASK_FAMILY_IDS = {
    "streaming_valid_ready": "valid_ready_stream_stage",
    "composed_event_counter": "t1_event_counter",
    "composed_stream_accumulator": "valid_ready_stream_accumulator",
    "composed_stream_fork": "stream_fork_join",
    "composed_dual_stream_join": "stream_fork_join",
    "composed_vector_mac_pipeline": "mac_array",
    "pattern_matcher": "pattern_matcher",
    "stream_trigger_filter": "p_stream_trigger_filter",
}


def streaming_valid_ready_testbench(width: int) -> str:
    msb = width - 1
    mask = (1 << width) - 1
    first_value = 0x12 & mask
    second_value = 0xA5 & mask
    if first_value == second_value:
        second_value = (~first_value) & mask
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          wire out_valid;
          reg out_ready;
          wire [{msb}:0] out_data;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_word;
            input [{msb}:0] value;
            begin
              @(negedge clk);
              in_data = value;
              in_valid = 1'b1;
              while (in_ready !== 1'b1) begin
                @(negedge clk);
              end
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task expect_word;
            input [{msb}:0] value;
            begin
              while (out_valid !== 1'b1) begin
                @(posedge clk);
              end
              #1;
              if (out_data !== value) begin
                $display("TEST_FAIL expected output %0d got %0d", value, out_data);
                $finish;
              end
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_word({width}'d{first_value});
            expect_word({width}'d{first_value});
            @(posedge clk);
            #1;

            out_ready = 1'b0;
            send_word({width}'d{second_value});
            repeat (2) @(posedge clk);
            #1;
            if (out_valid !== 1'b1) begin
              $display("TEST_FAIL stalled output was not held valid");
              $finish;
            end
            out_ready = 1'b1;
            expect_word({width}'d{second_value});
            @(posedge clk);
            #1;

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def streaming_valid_ready_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [{msb}:0] out_data
        );

          wire skid_valid;
          wire skid_ready;
          wire [{msb}:0] skid_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(skid_valid),
            .out_ready(skid_ready),
            .out_data(skid_data)
          );

          stream_stage #(
            .WIDTH({width})
          ) u_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(skid_valid),
            .in_ready(skid_ready),
            .in_data(skid_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
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
        "rtl/stream_stage.v": stream_stage,
    }


def composed_stream_accumulator_testbench(width: int) -> str:
    msb = width - 1
    sum_msb = width + 3
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          reg accum_ready;
          wire sample_valid;
          wire [{sum_msb}:0] sum;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .accum_ready(accum_ready),
            .sample_valid(sample_valid),
            .sum(sum)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_sample;
            input [{msb}:0] value;
            begin
              @(negedge clk);
              while (!in_ready) @(negedge clk);
              in_valid = 1'b1;
              in_data = value;
              @(negedge clk);
              in_valid = 1'b0;
              in_data = {width}'d0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            accum_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_sample({width}'d3);
            wait (sum == {width + 4}'d3);

            @(negedge clk);
            accum_ready = 1'b0;
            send_sample({width}'d4);
            repeat (3) begin
              @(posedge clk);
              #1;
              if (sample_valid !== 1'b1) begin
                $display("TEST_FAIL stalled sample_valid dropped");
                $finish;
              end
              if (sum !== {width + 4}'d3) begin
                $display("TEST_FAIL accumulator advanced while stalled sum=%0d", sum);
                $finish;
              end
            end

            @(negedge clk);
            accum_ready = 1'b1;
            @(posedge clk);
            #1;
            #1;

            if (sum !== {width + 4}'d7) begin
              $display("TEST_FAIL expected sum=7 got %0d", sum);
              $finish;
            end
            if (in_ready !== 1'b1) begin
              $display("TEST_FAIL in_ready not asserted");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def composed_stream_accumulator_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    sum_msb = width + 3
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            input wire accum_ready,
            output wire sample_valid,
            output wire [{sum_msb}:0] sum
        );

          wire [{msb}:0] sample_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(sample_valid),
            .out_ready(accum_ready),
            .out_data(sample_data)
          );

          accumulator_core #(
            .WIDTH({width}),
            .SUM_WIDTH({width + 4})
          ) u_accumulator_core (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample_ready(accum_ready),
            .sample(sample_data),
            .sum(sum)
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
    accumulator_core = dedent(
        """\
        module accumulator_core #(
            parameter WIDTH = 8,
            parameter SUM_WIDTH = 12
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            input wire sample_ready,
            input wire [WIDTH-1:0] sample,
            output reg [SUM_WIDTH-1:0] sum
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sum <= {SUM_WIDTH{1'b0}};
            end else if (sample_valid && sample_ready) begin
              sum <= sum + {{(SUM_WIDTH-WIDTH){1'b0}}, sample};
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/accumulator_core.v": accumulator_core,
    }


def composed_event_counter_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg event_valid;
          wire [{msb}:0] count;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .event_valid(event_valid),
            .count(count)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task pulse_event;
            begin
              @(negedge clk);
              event_valid = 1'b1;
              @(negedge clk);
              event_valid = 1'b0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            event_valid = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            pulse_event();
            pulse_event();
            repeat (2) @(posedge clk);
            #1;
            if (count !== {width}'d2) begin
              $display("TEST_FAIL expected count=2 got %0d", count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )

def composed_stream_fork_testbench(width: int) -> str:
    msb = width - 1
    first_value = min(0xA5, (1 << width) - 1)
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          wire out0_valid;
          reg out0_ready;
          wire [{msb}:0] out0_data;
          wire out1_valid;
          reg out1_ready;
          wire [{msb}:0] out1_data;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out0_valid(out0_valid),
            .out0_ready(out0_ready),
            .out0_data(out0_data),
            .out1_valid(out1_valid),
            .out1_ready(out1_ready),
            .out1_data(out1_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            out0_ready = 1'b0;
            out1_ready = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            in_valid = 1'b1;
            in_data = {width}'d{first_value};
            @(negedge clk);
            in_valid = 1'b0;
            in_data = {width}'d0;
            repeat (3) @(posedge clk);
            #1;

            if (out0_valid !== 1'b1 || out1_valid !== 1'b1) begin
              $display("TEST_FAIL fork outputs not valid");
              $finish;
            end
            if (out0_data !== {width}'d{first_value} || out1_data !== {width}'d{first_value}) begin
              $display("TEST_FAIL fork data mismatch out0=%0d out1=%0d", out0_data, out1_data);
              $finish;
            end
            @(negedge clk);
            out0_ready = 1'b1;
            out1_ready = 1'b1;
            @(posedge clk);
            #1;
            if (in_ready !== 1'b1) begin
              $display("TEST_FAIL fork input not ready");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )

def composed_dual_stream_join_testbench(width: int) -> str:
    msb = width - 1
    sum_width = width + 4
    sum_msb = sum_width - 1
    expected_pair_sum = 8
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in0_valid;
          wire in0_ready;
          reg [{msb}:0] in0_data;
          reg in1_valid;
          wire in1_ready;
          reg [{msb}:0] in1_data;
          wire out_valid;
          reg out_ready;
          wire [{sum_msb}:0] out_data;
          integer wait_cycles;
          reg [{sum_msb}:0] held_out_data;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in0_valid(in0_valid),
            .in0_ready(in0_ready),
            .in0_data(in0_data),
            .in1_valid(in1_valid),
            .in1_ready(in1_ready),
            .in1_data(in1_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            in0_valid = 1'b0;
            in0_data = {width}'d0;
            in1_valid = 1'b0;
            in1_data = {width}'d0;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            in0_valid = 1'b1;
            in0_data = {width}'d3;
            in1_valid = 1'b1;
            in1_data = {width}'d5;
            @(negedge clk);
            in0_valid = 1'b0;
            in1_valid = 1'b0;
            in0_data = {width}'d0;
            in1_data = {width}'d0;
            wait_cycles = 0;
            while (out_valid !== 1'b1 && wait_cycles < 8) begin
              @(posedge clk);
              #1;
              wait_cycles = wait_cycles + 1;
            end
            #1;

            if (out_valid !== 1'b1) begin
              $display("TEST_FAIL joined output not valid");
              $finish;
            end
            if (out_data !== {sum_width}'d{expected_pair_sum}) begin
              $display("TEST_FAIL expected joined sum=%0d got %0d", {expected_pair_sum}, out_data);
              $finish;
            end

            // Stall the output, fill both one-entry input buffers, and verify
            // that a third pair cannot overwrite the buffered transaction.
            @(negedge clk);
            out_ready = 1'b0;
            held_out_data = out_data;
            in0_valid = 1'b1;
            in0_data = {width}'d7;
            in1_valid = 1'b1;
            in1_data = {width}'d2;
            @(negedge clk);
            in0_valid = 1'b0;
            in1_valid = 1'b0;
            if (in0_ready !== 1'b0 || in1_ready !== 1'b0) begin
              $display("TEST_FAIL join missing_backpressure in0_ready=%0b in1_ready=%0b", in0_ready, in1_ready);
              $finish;
            end
            repeat (2) begin
              @(posedge clk);
              #1;
              if (out_valid !== 1'b1 || out_data !== held_out_data) begin
                $display("TEST_FAIL join output_changed_under_stall expected=%0d actual=%0d", held_out_data, out_data);
                $finish;
              end
            end

            @(negedge clk);
            out_ready = 1'b1;
            wait_cycles = 0;
            while ((out_valid !== 1'b1 || out_data !== {sum_width}'d17) && wait_cycles < 12) begin
              @(posedge clk);
              #1;
              wait_cycles = wait_cycles + 1;
            end
            if (out_valid !== 1'b1 || out_data !== {sum_width}'d17) begin
              $display("TEST_FAIL joined cumulative_sum expected=17 actual=%0d", out_data);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )

def composed_event_counter_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire event_valid,
            output wire [{msb}:0] count
        );

          wire count_en;

          event_gate u_event_gate (
            .event_valid(event_valid),
            .count_en(count_en)
          );

          counter_core #(
            .WIDTH({width})
          ) u_counter_core (
            .clk(clk),
            .rst_n(rst_n),
            .en(count_en),
            .count(count)
          );

        endmodule
        """
    )
    event_gate = dedent(
        """\
        module event_gate (
            input wire event_valid,
            output wire count_en
        );

          assign count_en = event_valid;

        endmodule
        """
    )
    counter_core = dedent(
        """\
        module counter_core #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire en,
            output reg [WIDTH-1:0] count
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              count <= {WIDTH{1'b0}};
            end else if (en) begin
              count <= count + {{(WIDTH-1){1'b0}}, 1'b1};
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/event_gate.v": event_gate,
        "rtl/counter_core.v": counter_core,
    }

def composed_stream_fork_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            output wire out0_valid,
            input wire out0_ready,
            output wire [{msb}:0] out0_data,
            output wire out1_valid,
            input wire out1_ready,
            output wire [{msb}:0] out1_data
        );

          wire fork_valid;
          wire fork_ready;
          wire [{msb}:0] fork_data;
          wire stage0_in_valid;
          wire stage0_in_ready;
          wire [{msb}:0] stage0_in_data;
          wire stage1_in_valid;
          wire stage1_in_ready;
          wire [{msb}:0] stage1_in_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(fork_valid),
            .out_ready(fork_ready),
            .out_data(fork_data)
          );

          stream_fork #(
            .WIDTH({width})
          ) u_stream_fork (
            .in_valid(fork_valid),
            .in_ready(fork_ready),
            .in_data(fork_data),
            .out0_valid(stage0_in_valid),
            .out0_ready(stage0_in_ready),
            .out0_data(stage0_in_data),
            .out1_valid(stage1_in_valid),
            .out1_ready(stage1_in_ready),
            .out1_data(stage1_in_data)
          );

          stream_stage #(
            .WIDTH({width})
          ) u_stage0 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(stage0_in_valid),
            .in_ready(stage0_in_ready),
            .in_data(stage0_in_data),
            .out_valid(out0_valid),
            .out_ready(out0_ready),
            .out_data(out0_data)
          );

          stream_stage #(
            .WIDTH({width})
          ) u_stage1 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(stage1_in_valid),
            .in_ready(stage1_in_ready),
            .in_data(stage1_in_data),
            .out_valid(out1_valid),
            .out_ready(out1_ready),
            .out_data(out1_data)
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
    stream_fork = dedent(
        """\
        module stream_fork #(
            parameter WIDTH = 8
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out0_valid,
            input wire out0_ready,
            output wire [WIDTH-1:0] out0_data,
            output wire out1_valid,
            input wire out1_ready,
            output wire [WIDTH-1:0] out1_data
        );

          assign in_ready = out0_ready && out1_ready;
          assign out0_valid = in_valid && out1_ready;
          assign out1_valid = in_valid && out0_ready;
          assign out0_data = in_data;
          assign out1_data = in_data;

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
        "rtl/stream_fork.v": stream_fork,
        "rtl/stream_stage.v": stream_stage,
    }

def pattern_matcher_testbench(width: int, project_mode: bool = False) -> str:
    msb = width - 1
    held_input_check = "" if project_mode else dedent(
        """\
            if (in_ready !== 1'b0) begin
              $display(\"TEST_FAIL matcher did not backpressure occupied output\");
              $finish;
            end
            @(negedge clk);
            in_valid = 1'b1;
            in_data = 8'hff;
            repeat (2) @(posedge clk);
            if (in_ready !== 1'b0) begin
              $display(\"TEST_FAIL matcher accepted input while output stalled\");
              $finish;
            end
            @(negedge clk);
            in_valid = 1'b0;
        """
    )
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          wire out_valid;
          reg out_ready;
          wire [31:0] out_match_index;
          wire [{width * 4 - 1}:0] out_match_word;
          reg [31:0] held_index;
          reg [{width * 4 - 1}:0] held_word;

          top dut (
            .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data),
            .out_valid(out_valid), .out_ready(out_ready), .out_match_index(out_match_index), .out_match_word(out_match_word)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task reset_dut;
            begin
              rst_n = 1'b0;
              in_valid = 1'b0;
              in_data = {width}'d0;
              out_ready = 1'b1;
              repeat (2) @(posedge clk);
              rst_n = 1'b1;
              @(negedge clk);
            end
          endtask

          task send_token;
            input [{msb}:0] value;
            begin
              @(negedge clk);
              in_data = value;
              in_valid = 1'b1;
              while (in_ready !== 1'b1) @(negedge clk);
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task expect_held_match;
            input [31:0] expected_index;
            input [{width * 4 - 1}:0] expected_word;
            integer cycles;
            begin
              cycles = 0;
              while (out_valid !== 1'b1 && cycles < 30) begin
                @(posedge clk);
                cycles = cycles + 1;
              end
              #1;
              if (out_valid !== 1'b1 || out_match_index !== expected_index || out_match_word !== expected_word) begin
                $display(\"TEST_FAIL match expected index=%0d word=%h got valid=%b index=%0d word=%h\", expected_index, expected_word, out_valid, out_match_index, out_match_word);
                $finish;
              end
              held_index = out_match_index;
              held_word = out_match_word;
              repeat (2) @(posedge clk);
              #1;
              if (out_valid !== 1'b1 || out_match_index !== held_index || out_match_word !== held_word) begin
                $display(\"TEST_FAIL output changed while stalled\");
                $finish;
              end
            end
          endtask

          task release_match;
            begin
              out_ready = 1'b1;
              @(posedge clk);
              @(negedge clk);
            end
          endtask

          initial begin
            reset_dut;
            out_ready = 1'b0;
            send_token(8'h11);
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h12);
            repeat (3) @(posedge clk);
            if (out_valid !== 1'b0) begin
              $display(\"TEST_FAIL false positive after partial pattern\");
              $finish;
            end

            reset_dut;
            send_token(8'h11);
            send_token(8'h22);
            reset_dut;
            out_ready = 1'b0;
            send_token(8'h11);
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h11);
            expect_held_match(32'd3, 32'h11223311);
{held_input_check.rstrip()}
            release_match;

            out_ready = 1'b0;
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h11);
            expect_held_match(32'd6, 32'h11223311);
            release_match;

            reset_dut;
            out_ready = 1'b0;
            send_token(8'h11);
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h11);
            expect_held_match(32'd3, 32'h11223311);
            release_match;

            $display(\"TEST_PASS\");
            $finish;
          end
        endmodule
        """
    )


def _pattern_matcher_source() -> str:
    return dedent(
        """\
        module pattern_matcher #(
            parameter WIDTH = 8,
            parameter [WIDTH-1:0] TOKEN0 = 8'h11,
            parameter [WIDTH-1:0] TOKEN1 = 8'h22,
            parameter [WIDTH-1:0] TOKEN2 = 8'h33,
            parameter [WIDTH-1:0] TOKEN3 = 8'h11
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output reg match_valid,
            input wire match_ready,
            output reg [31:0] match_index,
            output reg [WIDTH*4-1:0] match_word
        );

          reg [WIDTH-1:0] token0;
          reg [WIDTH-1:0] token1;
          reg [WIDTH-1:0] token2;
          reg [1:0] window_count;
          reg [31:0] accepted_index;

          assign in_ready = !match_valid || match_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              token0 <= {WIDTH{1'b0}};
              token1 <= {WIDTH{1'b0}};
              token2 <= {WIDTH{1'b0}};
              window_count <= 2'd0;
              accepted_index <= 32'd0;
              match_valid <= 1'b0;
              match_index <= 32'd0;
              match_word <= {(WIDTH*4){1'b0}};
            end else if (in_ready) begin
              match_valid <= 1'b0;
              if (in_valid) begin
                if (window_count == 2'd3 && token0 == TOKEN0 && token1 == TOKEN1 && token2 == TOKEN2 && in_data == TOKEN3) begin
                  match_valid <= 1'b1;
                  match_index <= accepted_index;
                  match_word <= {token0, token1, token2, in_data};
                end
                token0 <= token1;
                token1 <= token2;
                token2 <= in_data;
                if (window_count != 2'd3) begin
                  window_count <= window_count + 2'd1;
                end
                accepted_index <= accepted_index + 32'd1;
              end
            end
          end
        endmodule
        """
    )


def pattern_matcher_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top #(
            parameter WIDTH = {width},
            parameter [WIDTH-1:0] TOKEN0 = 8'h11,
            parameter [WIDTH-1:0] TOKEN1 = 8'h22,
            parameter [WIDTH-1:0] TOKEN2 = 8'h33,
            parameter [WIDTH-1:0] TOKEN3 = 8'h11
        ) (
            input wire clk, input wire rst_n, input wire in_valid, output wire in_ready,
            input wire [{msb}:0] in_data, output wire out_valid, input wire out_ready,
            output wire [31:0] out_match_index, output wire [{width * 4 - 1}:0] out_match_word
        );
          pattern_matcher #(.WIDTH(WIDTH), .TOKEN0(TOKEN0), .TOKEN1(TOKEN1), .TOKEN2(TOKEN2), .TOKEN3(TOKEN3)) u_pattern_matcher (
            .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data),
            .match_valid(out_valid), .match_ready(out_ready), .match_index(out_match_index), .match_word(out_match_word)
          );
        endmodule
        """
    )
    return {"rtl/top.v": top, "rtl/pattern_matcher.v": _pattern_matcher_source()}


def stream_trigger_filter_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top #(
            parameter WIDTH = {width},
            parameter [WIDTH-1:0] TOKEN0 = 8'h11,
            parameter [WIDTH-1:0] TOKEN1 = 8'h22,
            parameter [WIDTH-1:0] TOKEN2 = 8'h33,
            parameter [WIDTH-1:0] TOKEN3 = 8'h11
        ) (
            input wire clk, input wire rst_n, input wire in_valid, output wire in_ready,
            input wire [{msb}:0] in_data, output wire out_valid, input wire out_ready,
            output wire [31:0] out_match_index, output wire [{width * 4 - 1}:0] out_match_word
        );
          wire match_valid, match_ready;
          wire [31:0] match_index;
          wire [{width * 4 - 1}:0] match_word;
          wire trigger_valid, trigger_ready;
          wire [31:0] trigger_index;
          wire [{width * 4 - 1}:0] trigger_word;

          pattern_matcher #(.WIDTH(WIDTH), .TOKEN0(TOKEN0), .TOKEN1(TOKEN1), .TOKEN2(TOKEN2), .TOKEN3(TOKEN3)) u_pattern_matcher (
            .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data),
            .match_valid(match_valid), .match_ready(match_ready), .match_index(match_index), .match_word(match_word)
          );
          trigger_fsm #(.WIDTH(WIDTH)) u_trigger_fsm (
            .clk(clk), .rst_n(rst_n), .match_valid(match_valid), .match_ready(match_ready), .match_index(match_index), .match_word(match_word),
            .trigger_valid(trigger_valid), .trigger_ready(trigger_ready), .trigger_index(trigger_index), .trigger_word(trigger_word)
          );
          stream_packer #(.WIDTH(WIDTH)) u_stream_packer (
            .clk(clk), .rst_n(rst_n), .event_valid(trigger_valid), .event_ready(trigger_ready), .event_index(trigger_index), .event_word(trigger_word),
            .out_valid(out_valid), .out_ready(out_ready), .out_match_index(out_match_index), .out_match_word(out_match_word)
          );
        endmodule
        """
    )
    trigger_fsm = dedent(
        """\
        module trigger_fsm #(parameter WIDTH = 8) (
            input wire clk, input wire rst_n, input wire match_valid, output wire match_ready,
            input wire [31:0] match_index, input wire [WIDTH*4-1:0] match_word,
            output reg trigger_valid, input wire trigger_ready, output reg [31:0] trigger_index,
            output reg [WIDTH*4-1:0] trigger_word
        );
          assign match_ready = !trigger_valid || trigger_ready;
          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              trigger_valid <= 1'b0;
              trigger_index <= 32'd0;
              trigger_word <= {(WIDTH*4){1'b0}};
            end else if (match_ready) begin
              trigger_valid <= match_valid;
              if (match_valid) begin
                trigger_index <= match_index;
                trigger_word <= match_word;
              end
            end
          end
        endmodule
        """
    )
    stream_packer = dedent(
        """\
        module stream_packer #(parameter WIDTH = 8) (
            input wire clk, input wire rst_n, input wire event_valid, output wire event_ready,
            input wire [31:0] event_index, input wire [WIDTH*4-1:0] event_word,
            output reg out_valid, input wire out_ready, output reg [31:0] out_match_index,
            output reg [WIDTH*4-1:0] out_match_word
        );
          assign event_ready = !out_valid || out_ready;
          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              out_match_index <= 32'd0;
              out_match_word <= {(WIDTH*4){1'b0}};
            end else if (event_ready) begin
              out_valid <= event_valid;
              if (event_valid) begin
                out_match_index <= event_index;
                out_match_word <= event_word;
              end
            end
          end
        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/pattern_matcher.v": _pattern_matcher_source(),
        "rtl/trigger_fsm.v": trigger_fsm,
        "rtl/stream_packer.v": stream_packer,
    }


def composed_dual_stream_join_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    sum_width = width + 4
    sum_msb = sum_width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in0_valid,
            output wire in0_ready,
            input wire [{msb}:0] in0_data,
            input wire in1_valid,
            output wire in1_ready,
            input wire [{msb}:0] in1_data,
            output wire out_valid,
            input wire out_ready,
            output wire [{sum_msb}:0] out_data
        );

          wire s0_valid;
          wire s0_ready;
          wire [{msb}:0] s0_data;
          wire s1_valid;
          wire s1_ready;
          wire [{msb}:0] s1_data;
          wire joined_valid;
          wire [{msb}:0] joined_data;
          wire accum_valid;
          wire accum_ready;
          wire [{sum_msb}:0] accum_sum;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid0 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in0_valid),
            .in_ready(in0_ready),
            .in_data(in0_data),
            .out_valid(s0_valid),
            .out_ready(s0_ready),
            .out_data(s0_data)
          );

          skid_buffer #(
            .WIDTH({width})
          ) u_skid1 (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in1_valid),
            .in_ready(in1_ready),
            .in_data(in1_data),
            .out_valid(s1_valid),
            .out_ready(s1_ready),
            .out_data(s1_data)
          );

          stream_join #(
            .WIDTH({width})
          ) u_stream_join (
            .in0_valid(s0_valid),
            .in0_ready(s0_ready),
            .in0_data(s0_data),
            .in1_valid(s1_valid),
            .in1_ready(s1_ready),
            .in1_data(s1_data),
            .out_valid(joined_valid),
            .out_ready(accum_ready),
            .out_data(joined_data)
          );

          accumulator_core #(
            .WIDTH({width})
          ) u_accumulator_core (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(joined_valid),
            .sample_ready(accum_ready),
            .sample(joined_data),
            .sum(accum_sum)
          );

          assign accum_valid = joined_valid && accum_ready;

          stream_stage #(
            .WIDTH({sum_width})
          ) u_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(accum_valid),
            .in_ready(accum_ready),
            .in_data(accum_sum),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
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
    stream_join = dedent(
        """\
        module stream_join #(
            parameter WIDTH = 8
        ) (
            input wire in0_valid,
            output wire in0_ready,
            input wire [WIDTH-1:0] in0_data,
            input wire in1_valid,
            output wire in1_ready,
            input wire [WIDTH-1:0] in1_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          assign out_valid = in0_valid && in1_valid;
          assign in0_ready = out_ready && in1_valid;
          assign in1_ready = out_ready && in0_valid;
          assign out_data = in0_data + in1_data;

        endmodule
        """
    )
    accumulator_core = dedent(
        """\
        module accumulator_core #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            input wire sample_ready,
            input wire [WIDTH-1:0] sample,
            output wire [WIDTH+3:0] sum
        );

          reg [WIDTH+3:0] sum_r;

          assign sum = sum_r + ((sample_valid && sample_ready) ? {{4{1'b0}}, sample} : {(WIDTH+4){1'b0}});

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sum_r <= {(WIDTH+4){1'b0}};
            end else if (sample_valid && sample_ready) begin
              sum_r <= sum;
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
        "rtl/stream_join.v": stream_join,
        "rtl/accumulator_core.v": accumulator_core,
        "rtl/stream_stage.v": stream_stage,
    }
