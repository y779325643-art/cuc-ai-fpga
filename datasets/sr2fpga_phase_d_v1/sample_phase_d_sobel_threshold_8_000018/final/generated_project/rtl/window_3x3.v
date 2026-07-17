module window_3x3 #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire advance,
    input wire [DATA_WIDTH-1:0] row0_pixel,
    input wire [DATA_WIDTH-1:0] row1_pixel,
    input wire [DATA_WIDTH-1:0] row2_pixel,
    output wire window_valid,
    output wire [9*DATA_WIDTH-1:0] window_pixels
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] win_pixel_00;
    reg [DATA_WIDTH-1:0] win_pixel_01;
    reg [DATA_WIDTH-1:0] win_pixel_02;
    reg [DATA_WIDTH-1:0] win_pixel_10;
    reg [DATA_WIDTH-1:0] win_pixel_11;
    reg [DATA_WIDTH-1:0] win_pixel_12;
    reg [DATA_WIDTH-1:0] win_pixel_20;
    reg [DATA_WIDTH-1:0] win_pixel_21;
    reg [DATA_WIDTH-1:0] win_pixel_22;
    reg pipe_valid_window;
    reg [1:0] warmup_count_reg;

    assign window_valid = pipe_valid_window;
    assign window_pixels = {win_pixel_22, win_pixel_21, win_pixel_20,
                            win_pixel_12, win_pixel_11, win_pixel_10,
                            win_pixel_02, win_pixel_01, win_pixel_00};

    always @(posedge clk) begin
      if (!rst_n) begin
        win_pixel_00 <= {DATA_WIDTH{1'b0}};
        win_pixel_01 <= {DATA_WIDTH{1'b0}};
        win_pixel_02 <= {DATA_WIDTH{1'b0}};
        win_pixel_10 <= {DATA_WIDTH{1'b0}};
        win_pixel_11 <= {DATA_WIDTH{1'b0}};
        win_pixel_12 <= {DATA_WIDTH{1'b0}};
        win_pixel_20 <= {DATA_WIDTH{1'b0}};
        win_pixel_21 <= {DATA_WIDTH{1'b0}};
        win_pixel_22 <= {DATA_WIDTH{1'b0}};
        pipe_valid_window <= 1'b0;
        warmup_count_reg <= 2'b00;
      end else if (advance) begin
        win_pixel_00 <= win_pixel_01;
        win_pixel_01 <= win_pixel_02;
        win_pixel_02 <= row0_pixel;
        win_pixel_10 <= win_pixel_11;
        win_pixel_11 <= win_pixel_12;
        win_pixel_12 <= row1_pixel;
        win_pixel_20 <= win_pixel_21;
        win_pixel_21 <= win_pixel_22;
        win_pixel_22 <= row2_pixel;
        if (warmup_count_reg != 2'b11) begin
          warmup_count_reg <= warmup_count_reg + 2'b01;
        end
        pipe_valid_window <= (warmup_count_reg >= 2'b10);
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
