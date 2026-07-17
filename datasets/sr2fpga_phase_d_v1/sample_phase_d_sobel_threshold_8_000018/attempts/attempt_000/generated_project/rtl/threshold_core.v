module threshold_core #(parameter DATA_WIDTH = 8, parameter EDGE_HIGH_VALUE = 255, parameter EDGE_LOW_VALUE = 0) (
    input wire clk,
    input wire rst_n,
    input wire advance,
    input wire magnitude_valid,
    input wire [DATA_WIDTH+3-1:0] magnitude,
    input wire [DATA_WIDTH-1:0] threshold,
    input wire boundary,
    output wire edge_valid,
    output wire [DATA_WIDTH-1:0] edge_pixel,
    output wire edge_flag
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    localparam integer MAG_WIDTH = DATA_WIDTH + 3;

    reg edge_valid_reg;
    reg [DATA_WIDTH-1:0] edge_pixel_reg;
    reg edge_flag_reg;

    wire [MAG_WIDTH-1:0] threshold_ext = {{(MAG_WIDTH-DATA_WIDTH){1'b0}}, threshold};
    wire edge_compare = magnitude >= threshold_ext;
    wire [DATA_WIDTH-1:0] edge_high_sized = EDGE_HIGH_VALUE[DATA_WIDTH-1:0];
    wire [DATA_WIDTH-1:0] edge_low_sized = EDGE_LOW_VALUE[DATA_WIDTH-1:0];

    assign edge_valid = edge_valid_reg;
    assign edge_pixel = edge_pixel_reg;
    assign edge_flag = edge_flag_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        edge_valid_reg <= 1'b0;
        edge_pixel_reg <= edge_low_sized;
        edge_flag_reg <= 1'b0;
      end else if (advance) begin
        edge_valid_reg <= magnitude_valid;
        if (boundary || !magnitude_valid) begin
          edge_pixel_reg <= edge_low_sized;
          edge_flag_reg <= 1'b0;
        end else if (edge_compare) begin
          edge_pixel_reg <= edge_high_sized;
          edge_flag_reg <= 1'b1;
        end else begin
          edge_pixel_reg <= edge_low_sized;
          edge_flag_reg <= 1'b0;
        end
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
