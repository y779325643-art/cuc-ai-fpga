"""Deterministic streaming image task-family generators."""

from textwrap import dedent


TASK_FAMILY_IDS = {
    "sobel_threshold": "sobel_threshold",
    "vision_defect_core": "p_vision_defect_core",
}


def sobel_threshold_rtl_files(_width: int) -> dict[str, str]:
    """Emit an 8-bit, row-major Sobel threshold pipeline with two line buffers."""
    top = dedent(
        """\
        module top #(
            parameter IMAGE_WIDTH = 5,
            parameter IMAGE_HEIGHT = 5,
            parameter THRESHOLD = 100
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [7:0] in_pixel,
            input wire in_last,
            output reg out_valid,
            input wire out_ready,
            output reg out_edge,
            output reg edge_axis,
            output reg out_last
        );

          reg [15:0] row_index;
          reg [15:0] column_index;
          reg flush_right_pending;
          reg bottom_flush_active;
          reg final_input_last;
          reg frame_end_hold;
          reg [15:0] bottom_flush_column;
          wire accept_input;
          wire produces_output;
          wire window_valid;
          wire signed [10:0] gx;
          wire signed [10:0] gy;
          wire sobel_edge;
          /* verilator lint_off UNUSEDSIGNAL */
          wire sobel_axis;
          /* verilator lint_on UNUSEDSIGNAL */

          // A line-end or frame-end border is emitted internally before accepting more pixels.
          assign produces_output = (row_index == 16'd0) ||
              ((row_index >= 16'd2) && ((column_index == 16'd0) || (column_index >= 16'd2)));
          assign in_ready = !frame_end_hold && !flush_right_pending && !bottom_flush_active &&
              (!produces_output || !out_valid || out_ready);
          assign accept_input = in_valid && in_ready;

          sobel_window #(
            .IMAGE_WIDTH(IMAGE_WIDTH)
          ) u_sobel_window (
            .clk(clk),
            .rst_n(rst_n),
            .accept(accept_input),
            .row_index(row_index),
            .column_index(column_index),
            .in_pixel(in_pixel),
            .window_valid(window_valid),
            .gx(gx),
            .gy(gy)
          );

          sobel_threshold_core #(
            .THRESHOLD(THRESHOLD)
          ) u_sobel_threshold_core (
            .gx(gx),
            .gy(gy),
            .out_edge(sobel_edge),
            .edge_axis(sobel_axis)
          );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              row_index <= 16'd0;
              column_index <= 16'd0;
              flush_right_pending <= 1'b0;
              bottom_flush_active <= 1'b0;
              final_input_last <= 1'b0;
              frame_end_hold <= 1'b0;
              bottom_flush_column <= 16'd0;
              out_valid <= 1'b0;
              out_edge <= 1'b0;
              edge_axis <= 1'b0;
              out_last <= 1'b0;
            end else begin
              if (out_valid && out_ready) begin
                out_valid <= 1'b0;
              end

              if (flush_right_pending) begin
                if (!out_valid || out_ready) begin
                  out_valid <= 1'b1;
                  out_edge <= 1'b0;
                  edge_axis <= 1'b0;
                  out_last <= 1'b0;
                  flush_right_pending <= 1'b0;
                  if (row_index == IMAGE_HEIGHT - 1) begin
                    if (final_input_last) begin
                      bottom_flush_active <= 1'b1;
                      bottom_flush_column <= 16'd0;
                    end else begin
                      frame_end_hold <= 1'b1;
                    end
                  end else begin
                    row_index <= row_index + 16'd1;
                    column_index <= 16'd0;
                  end
                end
              end else if (bottom_flush_active) begin
                if (!out_valid || out_ready) begin
                  out_valid <= 1'b1;
                  out_edge <= 1'b0;
                  edge_axis <= 1'b0;
                  out_last <= (bottom_flush_column == IMAGE_WIDTH - 1);
                  if (bottom_flush_column == IMAGE_WIDTH - 1) begin
                    bottom_flush_active <= 1'b0;
                    final_input_last <= 1'b0;
                    row_index <= 16'd0;
                    column_index <= 16'd0;
                  end else begin
                    bottom_flush_column <= bottom_flush_column + 16'd1;
                  end
                end
              end else if (accept_input) begin
                if (produces_output) begin
                  out_valid <= 1'b1;
                  out_last <= 1'b0;
                  if (row_index == 16'd0) begin
                    out_edge <= 1'b0;
                    edge_axis <= 1'b0;
                  end else begin
                    out_edge <= window_valid && sobel_edge;
                    edge_axis <= window_valid && sobel_axis;
                  end
                end

                if (column_index == IMAGE_WIDTH - 1) begin
                  if (row_index >= 16'd2) begin
                    flush_right_pending <= 1'b1;
                    if (row_index == IMAGE_HEIGHT - 1) begin
                      final_input_last <= in_last;
                    end
                  end else begin
                    row_index <= row_index + 16'd1;
                    column_index <= 16'd0;
                  end
                end else begin
                  column_index <= column_index + 16'd1;
                end
              end
            end
          end
        endmodule
        """
    )
    line_buffer = dedent(
        """\
        module sobel_line_buffer #(
            parameter IMAGE_WIDTH = 5,
            parameter ADDR_WIDTH = (IMAGE_WIDTH <= 1) ? 1 : $clog2(IMAGE_WIDTH)
        ) (
            input wire clk,
            input wire write_en,
            input wire [ADDR_WIDTH-1:0] address,
            input wire [7:0] write_pixel,
            output wire [7:0] read_pixel
        );

          reg [7:0] pixels [0:IMAGE_WIDTH-1];

          assign read_pixel = pixels[address];

          always @(posedge clk) begin
            if (write_en) begin
              pixels[address] <= write_pixel;
            end
          end
        endmodule
        """
    )
    window = dedent(
        """\
        module sobel_window #(
            parameter IMAGE_WIDTH = 5,
            parameter ADDR_WIDTH = (IMAGE_WIDTH <= 1) ? 1 : $clog2(IMAGE_WIDTH)
        ) (
            input wire clk,
            input wire rst_n,
            input wire accept,
            input wire [15:0] row_index,
            input wire [15:0] column_index,
            input wire [7:0] in_pixel,
            output wire window_valid,
            output wire signed [10:0] gx,
            output wire signed [10:0] gy
        );

          wire select_line0;
          wire [7:0] line0_pixel;
          wire [7:0] line1_pixel;
          wire [7:0] top_pixel;
          wire [7:0] middle_pixel;
          reg [7:0] top_left;
          reg [7:0] top_middle;
          reg [7:0] middle_left;
          reg [7:0] middle_middle;
          reg [7:0] bottom_left;
          reg [7:0] bottom_middle;

          assign select_line0 = !row_index[0];
          assign top_pixel = select_line0 ? line0_pixel : line1_pixel;
          assign middle_pixel = select_line0 ? line1_pixel : line0_pixel;
          assign window_valid = accept && (row_index >= 16'd2) && (column_index >= 16'd2);

          sobel_line_buffer #(
            .IMAGE_WIDTH(IMAGE_WIDTH),
            .ADDR_WIDTH(ADDR_WIDTH)
          ) u_line_buffer_0 (
            .clk(clk),
            .write_en(accept && select_line0),
            .address(column_index[ADDR_WIDTH-1:0]),
            .write_pixel(in_pixel),
            .read_pixel(line0_pixel)
          );

          sobel_line_buffer #(
            .IMAGE_WIDTH(IMAGE_WIDTH),
            .ADDR_WIDTH(ADDR_WIDTH)
          ) u_line_buffer_1 (
            .clk(clk),
            .write_en(accept && !select_line0),
            .address(column_index[ADDR_WIDTH-1:0]),
            .write_pixel(in_pixel),
            .read_pixel(line1_pixel)
          );

          assign gx = -$signed({3'b000, top_left}) + $signed({3'b000, top_pixel})
              - ($signed({3'b000, middle_left}) <<< 1) + ($signed({3'b000, middle_pixel}) <<< 1)
              - $signed({3'b000, bottom_left}) + $signed({3'b000, in_pixel});
          assign gy = -$signed({3'b000, top_left}) - ($signed({3'b000, top_middle}) <<< 1)
              - $signed({3'b000, top_pixel}) + $signed({3'b000, bottom_left})
              + ($signed({3'b000, bottom_middle}) <<< 1) + $signed({3'b000, in_pixel});

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              top_left <= 8'd0;
              top_middle <= 8'd0;
              middle_left <= 8'd0;
              middle_middle <= 8'd0;
              bottom_left <= 8'd0;
              bottom_middle <= 8'd0;
            end else if (accept) begin
              top_left <= top_middle;
              top_middle <= top_pixel;
              middle_left <= middle_middle;
              middle_middle <= middle_pixel;
              bottom_left <= bottom_middle;
              bottom_middle <= in_pixel;
            end
          end
        endmodule
        """
    )
    core = dedent(
        """\
        module sobel_threshold_core #(
            parameter THRESHOLD = 100
        ) (
            input wire signed [10:0] gx,
            input wire signed [10:0] gy,
            output wire out_edge,
            output wire edge_axis
        );

          wire [10:0] abs_gx;
          wire [10:0] abs_gy;
          wire [11:0] magnitude;

          assign abs_gx = gx[10] ? -gx : gx;
          assign abs_gy = gy[10] ? -gy : gy;
          assign magnitude = abs_gx + abs_gy;
          assign out_edge = magnitude >= THRESHOLD;
          // edge_axis=1 is horizontal-gradient dominance: abs(Gx) >= abs(Gy).
          assign edge_axis = abs_gx >= abs_gy;
        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/sobel_line_buffer.v": line_buffer,
        "rtl/sobel_window.v": window,
        "rtl/sobel_threshold_core.v": core,
    }


def sobel_threshold_testbench() -> str:
    """Return a black-box 5x5 scoreboard for flat, axis, threshold, stall, and reset cases."""
    legacy = dedent(
        """\
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
            if (!rst_n) begin
              holding_output <= 1'b0;
            end else if (out_valid && !out_ready) begin
              if (holding_output && ((out_edge !== held_edge) || (edge_axis !== held_axis) || (out_last !== held_last))) begin
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

          initial begin
            rst_n = 1'b0;
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
        """
    )
    return _add_image_oracle_mode(legacy, vision=False)


def vision_defect_core_rtl_files(_width: int) -> dict[str, str]:
    """Emit the bounded Sobel defect contract without CCA or bounding boxes."""
    rtl_files = sobel_threshold_rtl_files(_width)
    rtl_files.pop("rtl/top.v")
    top = dedent(
        """\
        module top #(
            parameter IMAGE_WIDTH = 5,
            parameter IMAGE_HEIGHT = 5,
            parameter THRESHOLD = 100
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [7:0] in_pixel,
            input wire in_last,
            output reg out_valid,
            input wire out_ready,
            output reg out_edge,
            output reg out_last,
            output wire defect_present,
            output wire [15:0] first_defect_x,
            output wire [15:0] first_defect_y
        );

          reg [15:0] row_index;
          reg [15:0] column_index;
          reg flush_right_pending;
          reg bottom_flush_active;
          reg final_input_last;
          reg frame_end_hold;
          reg [15:0] bottom_flush_column;
          reg [15:0] output_row;
          reg [15:0] output_column;
          wire accept_input;
          wire produces_output;
          wire window_valid;
          wire signed [10:0] gx;
          wire signed [10:0] gy;
          wire sobel_edge;
          /* verilator lint_off UNUSEDSIGNAL */
          wire sobel_axis;
          /* verilator lint_on UNUSEDSIGNAL */
          wire accumulated_defect_present;
          wire [15:0] accumulated_first_defect_x;
          wire [15:0] accumulated_first_defect_y;
          wire reported_defect_present;
          wire [15:0] reported_first_defect_x;
          wire [15:0] reported_first_defect_y;
          wire accept_output;

          assign produces_output = (row_index == 16'd0) ||
              ((row_index >= 16'd2) && ((column_index == 16'd0) || (column_index >= 16'd2)));
          assign in_ready = !frame_end_hold && !flush_right_pending && !bottom_flush_active &&
              (!produces_output || !out_valid || out_ready);
          assign accept_input = in_valid && in_ready;
          assign accept_output = out_valid && out_ready;
          // The frame report is defined on the out_last beat. Other beats do not carry a frame result.
          assign defect_present = out_last ? accumulated_defect_present : reported_defect_present;
          assign first_defect_x = out_last ? accumulated_first_defect_x : reported_first_defect_x;
          assign first_defect_y = out_last ? accumulated_first_defect_y : reported_first_defect_y;

          sobel_window #(
            .IMAGE_WIDTH(IMAGE_WIDTH)
          ) u_sobel_window (
            .clk(clk),
            .rst_n(rst_n),
            .accept(accept_input),
            .row_index(row_index),
            .column_index(column_index),
            .in_pixel(in_pixel),
            .window_valid(window_valid),
            .gx(gx),
            .gy(gy)
          );

          sobel_threshold_core #(
            .THRESHOLD(THRESHOLD)
          ) u_sobel_threshold_core (
            .gx(gx),
            .gy(gy),
            .out_edge(sobel_edge),
            .edge_axis(sobel_axis)
          );

          vision_defect_accumulator u_vision_defect_accumulator (
            .clk(clk),
            .rst_n(rst_n),
            .pixel_accept(accept_output),
            .pixel_edge(out_edge),
            .pixel_x(output_column),
            .pixel_y(output_row),
            .frame_end(accept_output && out_last),
            .defect_present(accumulated_defect_present),
            .first_defect_x(accumulated_first_defect_x),
            .first_defect_y(accumulated_first_defect_y)
          );

          vision_io_control u_vision_io_control (
            .clk(clk),
            .rst_n(rst_n),
            .frame_report_accept(accept_output && out_last),
            .defect_present(accumulated_defect_present),
            .first_defect_x(accumulated_first_defect_x),
            .first_defect_y(accumulated_first_defect_y),
            .reported_defect_present(reported_defect_present),
            .reported_first_defect_x(reported_first_defect_x),
            .reported_first_defect_y(reported_first_defect_y)
          );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              output_row <= 16'd0;
              output_column <= 16'd0;
            end else if (accept_output) begin
              if (out_last) begin
                output_row <= 16'd0;
                output_column <= 16'd0;
              end else if (output_column == IMAGE_WIDTH - 1) begin
                output_row <= output_row + 16'd1;
                output_column <= 16'd0;
              end else begin
                output_column <= output_column + 16'd1;
              end
            end
          end

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              row_index <= 16'd0;
              column_index <= 16'd0;
              flush_right_pending <= 1'b0;
              bottom_flush_active <= 1'b0;
              final_input_last <= 1'b0;
              frame_end_hold <= 1'b0;
              bottom_flush_column <= 16'd0;
              out_valid <= 1'b0;
              out_edge <= 1'b0;
              out_last <= 1'b0;
            end else begin
              if (out_valid && out_ready) begin
                out_valid <= 1'b0;
              end

              if (flush_right_pending) begin
                if (!out_valid || out_ready) begin
                  out_valid <= 1'b1;
                  out_edge <= 1'b0;
                  out_last <= 1'b0;
                  flush_right_pending <= 1'b0;
                  if (row_index == IMAGE_HEIGHT - 1) begin
                    if (final_input_last) begin
                      bottom_flush_active <= 1'b1;
                      bottom_flush_column <= 16'd0;
                    end else begin
                      frame_end_hold <= 1'b1;
                    end
                  end else begin
                    row_index <= row_index + 16'd1;
                    column_index <= 16'd0;
                  end
                end
              end else if (bottom_flush_active) begin
                if (!out_valid || out_ready) begin
                  out_valid <= 1'b1;
                  out_edge <= 1'b0;
                  out_last <= (bottom_flush_column == IMAGE_WIDTH - 1);
                  if (bottom_flush_column == IMAGE_WIDTH - 1) begin
                    bottom_flush_active <= 1'b0;
                    final_input_last <= 1'b0;
                    row_index <= 16'd0;
                    column_index <= 16'd0;
                  end else begin
                    bottom_flush_column <= bottom_flush_column + 16'd1;
                  end
                end
              end else if (accept_input) begin
                if (produces_output) begin
                  out_valid <= 1'b1;
                  out_last <= 1'b0;
                  if (row_index == 16'd0) begin
                    out_edge <= 1'b0;
                  end else begin
                    out_edge <= window_valid && sobel_edge;
                  end
                end

                if (column_index == IMAGE_WIDTH - 1) begin
                  if (row_index >= 16'd2) begin
                    flush_right_pending <= 1'b1;
                    if (row_index == IMAGE_HEIGHT - 1) begin
                      final_input_last <= in_last;
                    end
                  end else begin
                    row_index <= row_index + 16'd1;
                    column_index <= 16'd0;
                  end
                end else begin
                  column_index <= column_index + 16'd1;
                end
              end
            end
          end
        endmodule
        """
    )
    accumulator = dedent(
        """\
        module vision_defect_accumulator (
            input wire clk,
            input wire rst_n,
            input wire pixel_accept,
            input wire pixel_edge,
            input wire [15:0] pixel_x,
            input wire [15:0] pixel_y,
            input wire frame_end,
            output reg defect_present,
            output reg [15:0] first_defect_x,
            output reg [15:0] first_defect_y
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              defect_present <= 1'b0;
              first_defect_x <= 16'd0;
              first_defect_y <= 16'd0;
            end else if (frame_end) begin
              defect_present <= 1'b0;
              first_defect_x <= 16'd0;
              first_defect_y <= 16'd0;
            end else if (pixel_accept && pixel_edge && !defect_present) begin
              defect_present <= 1'b1;
              first_defect_x <= pixel_x;
              first_defect_y <= pixel_y;
            end
          end
        endmodule
        """
    )
    io_control = dedent(
        """\
        module vision_io_control (
            input wire clk,
            input wire rst_n,
            input wire frame_report_accept,
            input wire defect_present,
            input wire [15:0] first_defect_x,
            input wire [15:0] first_defect_y,
            output reg reported_defect_present,
            output reg [15:0] reported_first_defect_x,
            output reg [15:0] reported_first_defect_y
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              reported_defect_present <= 1'b0;
              reported_first_defect_x <= 16'd0;
              reported_first_defect_y <= 16'd0;
            end else if (frame_report_accept) begin
              reported_defect_present <= defect_present;
              reported_first_defect_x <= first_defect_x;
              reported_first_defect_y <= first_defect_y;
            end
          end
        endmodule
        """
    )
    rtl_files.update(
        {
            "rtl/top.v": top,
            "rtl/vision_defect_accumulator.v": accumulator,
            "rtl/vision_io_control.v": io_control,
        }
    )
    return rtl_files


def vision_defect_core_testbench() -> str:
    """Return a black-box bounded-frame defect scoreboard."""
    legacy = dedent(
        """\
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
            if (!rst_n) begin
              holding_output <= 1'b0;
            end else if (out_valid && !out_ready) begin
              if (holding_output && ((out_edge !== held_edge) || (out_last !== held_last) ||
                  (defect_present !== held_defect) || (first_defect_x !== held_x) || (first_defect_y !== held_y))) begin
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

          initial begin
            rst_n = 1'b0;
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
        """
    )
    return _add_image_oracle_mode(legacy, vision=True)


def _add_image_oracle_mode(testbench: str, *, vision: bool) -> str:
    expected_width = 36 if vision else 4
    declaration_marker = "  reg [15:0] held_y;\n" if vision else "  reg held_last;\n"
    declarations = dedent(
        f"""\
          string oracle_input_path;
          string oracle_expected_path;
          string oracle_scenario_id;
          string oracle_scenario_class;
          integer oracle_transaction_count;
          integer oracle_mode;
          reg oracle_active;
          reg [23:0] oracle_input_memory [0:4095];
          reg [{expected_width - 1}:0] oracle_expected_memory [0:4095];
          reg [23:0] oracle_input_record;
          integer oracle_output_index;
          integer oracle_expected_output_count;
          integer oracle_expected_final_frame_count;
          integer oracle_frame_output_count;
          integer oracle_wait_count;
          integer oracle_stall_index;
          integer oracle_stall_cycles;
          integer oracle_drain_target;
          localparam integer ORACLE_EXPECT_OUTPUT_BIT = {35 if vision else 3};
          localparam integer ORACLE_OUT_LAST_BIT = {1 if vision else 2};
        """
    )
    testbench = _insert_after_once(testbench, declaration_marker, declarations)

    monitor_marker = "  always @(posedge clk) begin\n    if (!rst_n) begin\n      holding_output"
    monitor = _vision_oracle_monitor() if vision else _sobel_oracle_monitor()
    testbench = _insert_before_once(testbench, monitor_marker, monitor)

    stability_failure = '        $display("TEST_FAIL output changed under stall");\n'
    stability_json = dedent(
        """\
                if (oracle_active) begin
                  $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"field\\\":\\\"output_stability\\\",\\\"expected\\\":\\\"stable\\\",\\\"actual\\\":\\\"changed\\\"}",
                           oracle_scenario_id, oracle_scenario_class, oracle_output_index);
                end
        """
    ) + stability_failure
    testbench = _replace_once(testbench, stability_failure, stability_json)

    task_marker = "  initial begin\n    rst_n = 1'b0;\n"
    testbench = _insert_before_once(testbench, task_marker, _oracle_driver_task())
    oracle_start = dedent(
        """\
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
        """
    )
    testbench = _insert_after_once(testbench, task_marker, oracle_start)
    return testbench


def _sobel_oracle_monitor() -> str:
    return dedent(
        """\
          always @(posedge clk) begin
            if (rst_n && oracle_active && out_valid && out_ready) begin
              if (oracle_output_index >= oracle_expected_output_count || oracle_frame_output_count >= 25) begin
                $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"field\\\":\\\"output_count\\\",\\\"expected\\\":\\\"at_most_25_per_frame\\\",\\\"actual\\\":\\\"overflow\\\"}",
                         oracle_scenario_id, oracle_scenario_class, oracle_output_index);
                $display("TEST_FAIL emitted more than 25 pixels");
                $finish;
              end
              if (out_edge !== oracle_expected_memory[oracle_output_index][0] ||
                  edge_axis !== oracle_expected_memory[oracle_output_index][1] ||
                  out_last !== oracle_expected_memory[oracle_output_index][2]) begin
                $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{\\\"edge\\\":%0d,\\\"axis\\\":%0d,\\\"out_last\\\":%0d},\\\"actual\\\":{\\\"edge\\\":\\\"%0b\\\",\\\"axis\\\":\\\"%0b\\\",\\\"out_last\\\":\\\"%0b\\\"}}",
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

        """
    )


def _vision_oracle_monitor() -> str:
    return dedent(
        """\
          always @(posedge clk) begin
            if (rst_n && oracle_active && out_valid && out_ready) begin
              if (oracle_output_index >= oracle_expected_output_count || oracle_frame_output_count >= 25) begin
                $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"field\\\":\\\"output_count\\\",\\\"expected\\\":\\\"at_most_25_per_frame\\\",\\\"actual\\\":\\\"overflow\\\"}",
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
                $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"expected\\\":{\\\"edge\\\":%0d,\\\"out_last\\\":%0d,\\\"defect_present\\\":%0d,\\\"first_x\\\":%0d,\\\"first_y\\\":%0d},\\\"actual\\\":{\\\"edge\\\":\\\"%0b\\\",\\\"out_last\\\":\\\"%0b\\\",\\\"defect_present\\\":\\\"%0b\\\",\\\"first_x\\\":%0d,\\\"first_y\\\":%0d}}",
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

        """
    )


def _oracle_driver_task() -> str:
    return dedent(
        """\
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
                    $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"field\\\":\\\"pre_reset_drain\\\",\\\"expected\\\":%0d,\\\"actual\\\":%0d}",
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
                  $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"field\\\":\\\"in_ready\\\",\\\"expected\\\":1,\\\"actual\\\":\\\"%0b\\\"}",
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
                      $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"field\\\":\\\"input_backpressure\\\",\\\"expected\\\":0,\\\"actual\\\":\\\"%0b\\\"}",
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
                $display("SR2FPGA_MISMATCH {\\\"scenario_id\\\":\\\"%0s\\\",\\\"class\\\":\\\"%0s\\\",\\\"item_index\\\":%0d,\\\"field\\\":\\\"output_count\\\",\\\"expected\\\":%0d,\\\"actual\\\":%0d}",
                         oracle_scenario_id, oracle_scenario_class, oracle_output_index,
                         oracle_expected_output_count, oracle_output_index);
                $display("TEST_FAIL timeout outputs=%0d", oracle_output_index);
                $finish;
              end
              $display("TEST_PASS");
              $finish;
            end
          endtask

        """
    )


def _insert_after_once(source: str, marker: str, addition: str) -> str:
    if source.count(marker) != 1:
        raise RuntimeError(f"expected one image testbench marker, found {source.count(marker)}")
    return source.replace(marker, marker + addition, 1)


def _insert_before_once(source: str, marker: str, addition: str) -> str:
    if source.count(marker) != 1:
        raise RuntimeError(f"expected one image testbench marker, found {source.count(marker)}")
    return source.replace(marker, addition + marker, 1)


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"expected one image testbench marker, found {source.count(old)}")
    return source.replace(old, new, 1)
