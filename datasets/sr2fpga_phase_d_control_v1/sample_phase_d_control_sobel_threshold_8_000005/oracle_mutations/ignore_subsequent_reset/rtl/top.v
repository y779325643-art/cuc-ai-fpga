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
  reg mutation_reset_seen;
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
    if (!rst_n && mutation_reset_seen !== 1'b1) begin
      mutation_reset_seen <= 1'b1;
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
