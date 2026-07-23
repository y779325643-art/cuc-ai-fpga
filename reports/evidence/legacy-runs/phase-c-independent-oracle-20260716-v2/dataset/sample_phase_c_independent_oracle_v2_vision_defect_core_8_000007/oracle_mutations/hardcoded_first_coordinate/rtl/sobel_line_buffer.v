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
