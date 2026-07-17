module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire sample_ready,
    input wire [DATA_WIDTH-1:0] sample_data,
    output wire accum_valid,
    input wire accum_ready,
    output wire [DATA_WIDTH-1:0] accum_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] accumulator_sum_reg;
    wire [DATA_WIDTH:0] accumulator_sum_ext;
    wire transfer_en;

    assign transfer_en = sample_valid & sample_ready;
    assign accumulator_sum_ext = {1'b0, accumulator_sum_reg} + {1'b0, sample_data};
    wire _unused_accumulator_carry = accumulator_sum_ext[DATA_WIDTH];

    assign accum_valid = sample_valid & sample_ready;
    assign accum_data = accumulator_sum_ext[DATA_WIDTH-1:0];
    assign sample_ready = accum_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        accumulator_sum_reg <= {DATA_WIDTH{1'b0}};
      end else if (transfer_en) begin
        accumulator_sum_reg <= accumulator_sum_ext[DATA_WIDTH-1:0];
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
