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

  assign select_line0 = 1'b0;
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
