module shift_register #(parameter DATA_WIDTH = 8, parameter DEPTH = 3) (
    input wire clk,
    input wire rst_n,
    input wire shift_en,
    input wire [DATA_WIDTH-1:0] data_in,
    output wire [DATA_WIDTH-1:0] tap_0,
    output wire [DATA_WIDTH-1:0] tap_1,
    output wire [DATA_WIDTH-1:0] tap_2
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  reg [DATA_WIDTH-1:0] tap_0_reg;
  reg [DATA_WIDTH-1:0] tap_1_reg;
  reg [DATA_WIDTH-1:0] tap_2_reg;

  assign tap_0 = tap_0_reg;
  assign tap_1 = tap_1_reg;
  assign tap_2 = tap_2_reg;

  always @(posedge clk) begin
     if (!rst_n) begin
        tap_0_reg <= {DATA_WIDTH{1'b0}};
        tap_1_reg <= {DATA_WIDTH{1'b0}};
        tap_2_reg <= {DATA_WIDTH{1'b0}};
     end else if (shift_en) begin
        tap_0_reg <= data_in;
        tap_1_reg <= tap_0_reg;
        tap_2_reg <= tap_1_reg;
     end
  end
  // SR2FPGA_BEHAVIOR_END
endmodule
