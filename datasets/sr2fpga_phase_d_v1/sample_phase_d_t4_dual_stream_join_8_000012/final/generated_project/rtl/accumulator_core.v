module accumulator_core #(parameter DATA_WIDTH = 8, parameter ACCUM_WIDTH = 16) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [2*DATA_WIDTH-1:0] sample_data,
    input wire sample_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    output wire in_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  reg [ACCUM_WIDTH-1:0] accum_sum_reg;
  reg out_valid_reg;
  reg [DATA_WIDTH-1:0] out_data_reg;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      accum_sum_reg <= 0;
      out_valid_reg <= 0;
      out_data_reg <= 0;
    end else begin
      if (sample_valid && sample_ready && !out_valid_reg) begin
        wire [ACCUM_WIDTH:0] sum_ext = {1'b0, accum_sum_reg} + {1'b0, sample_data};
        accum_sum_reg <= sum_ext[ACCUM_WIDTH-1:0];
        out_data_reg <= sum_ext[DATA_WIDTH-1:0];
        out_valid_reg <= 1'b1;
      end else if (sample_ready && out_valid_reg) begin
        out_valid_reg <= 1'b0;
      end
    end
  end

  always_comb begin
    in_ready  = sample_ready && !out_valid_reg;
    out_valid = out_valid_reg;
    out_data  = out_data_reg;
  end
  // SR2FPGA_BEHAVIOR_END
endmodule
