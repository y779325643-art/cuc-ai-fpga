module top #(parameter DATA_WIDTH = 8, parameter IMG_WIDTH = 640, parameter IMG_HEIGHT = 480, parameter EDGE_HIGH_VALUE = 255, parameter EDGE_LOW_VALUE = 0) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] in_pixel,
    input wire in_last,
    input wire [DATA_WIDTH-1:0] threshold,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_pixel,
    output wire out_edge,
    output wire out_last
);

  wire u_ctrl__in_valid;
  wire u_ctrl__in_ready;
  wire u_ctrl__in_last;
  wire u_ctrl__advance;
  wire u_ctrl__boundary;
  wire u_ctrl__last_aligned;
  wire u_line_buffer__advance;
  wire [DATA_WIDTH-1:0] u_line_buffer__pixel_in;
  wire [DATA_WIDTH-1:0] u_line_buffer__row0_pixel;
  wire [DATA_WIDTH-1:0] u_line_buffer__row1_pixel;
  wire [DATA_WIDTH-1:0] u_line_buffer__row2_pixel;
  wire u_window__advance;
  wire [DATA_WIDTH-1:0] u_window__row0_pixel;
  wire [DATA_WIDTH-1:0] u_window__row1_pixel;
  wire [DATA_WIDTH-1:0] u_window__row2_pixel;
  wire u_window__window_valid;
  wire [9*DATA_WIDTH-1:0] u_window__window_pixels;
  wire u_sobel__advance;
  wire u_sobel__window_valid;
  wire [9*DATA_WIDTH-1:0] u_sobel__window_pixels;
  wire u_sobel__magnitude_valid;
  wire [DATA_WIDTH+3-1:0] u_sobel__magnitude;
  wire u_threshold__advance;
  wire u_threshold__magnitude_valid;
  wire [DATA_WIDTH+3-1:0] u_threshold__magnitude;
  wire [DATA_WIDTH-1:0] u_threshold__threshold;
  wire u_threshold__boundary;
  wire u_threshold__edge_valid;
  wire [DATA_WIDTH-1:0] u_threshold__edge_pixel;
  wire u_threshold__edge_flag;

  assign u_line_buffer__pixel_in = in_pixel;
  assign u_window__row0_pixel = u_line_buffer__row2_pixel;
  assign u_sobel__window_pixels = u_window__window_pixels;
  assign u_threshold__magnitude = u_sobel__magnitude;
  assign u_threshold__magnitude_valid = u_sobel__magnitude_valid;
  assign u_threshold__threshold = threshold;
  assign out_pixel = u_threshold__edge_flag;
  assign u_ctrl__in_last = in_last;
  assign out_last = u_ctrl__last_aligned;

  stream_control #(.IMG_WIDTH(IMG_WIDTH), .IMG_HEIGHT(IMG_HEIGHT)) u_ctrl (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(u_ctrl__in_valid),
    .in_ready(u_ctrl__in_ready),
    .in_last(u_ctrl__in_last),
    .advance(u_ctrl__advance),
    .boundary(u_ctrl__boundary),
    .last_aligned(u_ctrl__last_aligned)
  );

  line_buffer #(.DATA_WIDTH(DATA_WIDTH), .IMG_WIDTH(IMG_WIDTH)) u_line_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .advance(u_line_buffer__advance),
    .pixel_in(u_line_buffer__pixel_in),
    .row0_pixel(u_line_buffer__row0_pixel),
    .row1_pixel(u_line_buffer__row1_pixel),
    .row2_pixel(u_line_buffer__row2_pixel)
  );

  window_3x3 #(.DATA_WIDTH(DATA_WIDTH)) u_window (
    .clk(clk),
    .rst_n(rst_n),
    .advance(u_window__advance),
    .row0_pixel(u_window__row0_pixel),
    .row1_pixel(u_window__row1_pixel),
    .row2_pixel(u_window__row2_pixel),
    .window_valid(u_window__window_valid),
    .window_pixels(u_window__window_pixels)
  );

  sobel_core #(.DATA_WIDTH(DATA_WIDTH)) u_sobel (
    .clk(clk),
    .rst_n(rst_n),
    .advance(u_sobel__advance),
    .window_valid(u_sobel__window_valid),
    .window_pixels(u_sobel__window_pixels),
    .magnitude_valid(u_sobel__magnitude_valid),
    .magnitude(u_sobel__magnitude)
  );

  threshold_core #(.DATA_WIDTH(DATA_WIDTH), .EDGE_HIGH_VALUE(EDGE_HIGH_VALUE), .EDGE_LOW_VALUE(EDGE_LOW_VALUE)) u_threshold (
    .clk(clk),
    .rst_n(rst_n),
    .advance(u_threshold__advance),
    .magnitude_valid(u_threshold__magnitude_valid),
    .magnitude(u_threshold__magnitude),
    .threshold(u_threshold__threshold),
    .boundary(u_threshold__boundary),
    .edge_valid(u_threshold__edge_valid),
    .edge_pixel(u_threshold__edge_pixel),
    .edge_flag(u_threshold__edge_flag)
  );

endmodule
