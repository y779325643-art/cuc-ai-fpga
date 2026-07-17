module sobel_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire advance,
    input wire window_valid,
    input wire [9*DATA_WIDTH-1:0] window_pixels,
    output wire magnitude_valid,
    output wire [DATA_WIDTH+3-1:0] magnitude
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    localparam integer MAG_WIDTH = DATA_WIDTH + 3;
    localparam integer GRAD_WIDTH = DATA_WIDTH + 3;

    wire [DATA_WIDTH-1:0] p00 = window_pixels[(0*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p01 = window_pixels[(1*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p02 = window_pixels[(2*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p10 = window_pixels[(3*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p12 = window_pixels[(5*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p20 = window_pixels[(6*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p21 = window_pixels[(7*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p22 = window_pixels[(8*DATA_WIDTH) +: DATA_WIDTH];
    wire [DATA_WIDTH-1:0] p11_unused = window_pixels[(4*DATA_WIDTH) +: DATA_WIDTH];
    wire _unused_center_pixel = &{1'b0, p11_unused};

    wire signed [GRAD_WIDTH-1:0] p00_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p00});
    wire signed [GRAD_WIDTH-1:0] p01_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p01});
    wire signed [GRAD_WIDTH-1:0] p02_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p02});
    wire signed [GRAD_WIDTH-1:0] p10_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p10});
    wire signed [GRAD_WIDTH-1:0] p12_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p12});
    wire signed [GRAD_WIDTH-1:0] p20_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p20});
    wire signed [GRAD_WIDTH-1:0] p21_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p21});
    wire signed [GRAD_WIDTH-1:0] p22_s = $signed({{(GRAD_WIDTH-DATA_WIDTH){1'b0}}, p22});

    wire signed [GRAD_WIDTH-1:0] gx_calc = (p02_s + (p12_s <<< 1) + p22_s) - (p00_s + (p10_s <<< 1) + p20_s);
    wire signed [GRAD_WIDTH-1:0] gy_calc = (p20_s + (p21_s <<< 1) + p22_s) - (p00_s + (p01_s <<< 1) + p02_s);
    wire [GRAD_WIDTH-1:0] gx_abs = gx_calc[GRAD_WIDTH-1] ? $unsigned(-gx_calc) : $unsigned(gx_calc);
    wire [GRAD_WIDTH-1:0] gy_abs = gy_calc[GRAD_WIDTH-1] ? $unsigned(-gy_calc) : $unsigned(gy_calc);
    wire [MAG_WIDTH:0] magnitude_sum = {1'b0, gx_abs} + {1'b0, gy_abs};

    reg magnitude_valid_reg;
    reg [MAG_WIDTH-1:0] magnitude_reg;

    assign magnitude_valid = magnitude_valid_reg;
    assign magnitude = magnitude_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        magnitude_valid_reg <= 1'b0;
        magnitude_reg <= {MAG_WIDTH{1'b0}};
      end else if (advance) begin
        magnitude_valid_reg <= window_valid;
        if (magnitude_sum[MAG_WIDTH]) begin
          magnitude_reg <= {MAG_WIDTH{1'b1}};
        end else begin
          magnitude_reg <= magnitude_sum[MAG_WIDTH-1:0];
        end
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
