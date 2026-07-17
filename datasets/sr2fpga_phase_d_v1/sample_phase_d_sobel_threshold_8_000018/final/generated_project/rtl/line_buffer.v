module line_buffer #(parameter DATA_WIDTH = 8, parameter IMG_WIDTH = 640) (
    input wire clk,
    input wire rst_n,
    input wire advance,
    input wire [DATA_WIDTH-1:0] pixel_in,
    output wire [DATA_WIDTH-1:0] row0_pixel,
    output wire [DATA_WIDTH-1:0] row1_pixel,
    output wire [DATA_WIDTH-1:0] row2_pixel
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    localparam integer ADDR_WIDTH = (IMG_WIDTH <= 2) ? 1 : $clog2(IMG_WIDTH);

    reg [DATA_WIDTH-1:0] lb_row0_mem [0:IMG_WIDTH-1];
    reg [DATA_WIDTH-1:0] lb_row1_mem [0:IMG_WIDTH-1];
    reg [ADDR_WIDTH-1:0] write_addr_reg;
    reg [DATA_WIDTH-1:0] row0_pixel_reg;
    reg [DATA_WIDTH-1:0] row1_pixel_reg;
    reg [DATA_WIDTH-1:0] row2_pixel_reg;

    assign row0_pixel = row0_pixel_reg;
    assign row1_pixel = row1_pixel_reg;
    assign row2_pixel = row2_pixel_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        write_addr_reg <= {ADDR_WIDTH{1'b0}};
        row0_pixel_reg <= {DATA_WIDTH{1'b0}};
        row1_pixel_reg <= {DATA_WIDTH{1'b0}};
        row2_pixel_reg <= {DATA_WIDTH{1'b0}};
      end else if (advance) begin
        row0_pixel_reg <= lb_row0_mem[write_addr_reg];
        row1_pixel_reg <= lb_row1_mem[write_addr_reg];
        row2_pixel_reg <= pixel_in;
        lb_row0_mem[write_addr_reg] <= lb_row1_mem[write_addr_reg];
        lb_row1_mem[write_addr_reg] <= pixel_in;
        if (write_addr_reg == IMG_WIDTH[ADDR_WIDTH-1:0] - {{(ADDR_WIDTH-1){1'b0}}, 1'b1}) begin
          write_addr_reg <= {ADDR_WIDTH{1'b0}};
        end else begin
          write_addr_reg <= write_addr_reg + {{(ADDR_WIDTH-1){1'b0}}, 1'b1};
        end
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
