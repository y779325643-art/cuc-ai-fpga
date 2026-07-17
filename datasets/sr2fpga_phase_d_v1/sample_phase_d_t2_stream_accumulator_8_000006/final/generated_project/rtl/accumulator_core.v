module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [DATA_WIDTH-1:0] sample,
    input wire sample_ready,
    output wire [DATA_WIDTH-1:0] sum
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] accumulator_sum_reg;
    reg [31:0] accepted_sample_count;
    wire [DATA_WIDTH:0] accumulator_sum_ext;

    assign accumulator_sum_ext = {1'b0, accumulator_sum_reg} + {1'b0, sample};
    assign sum = accumulator_sum_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        accumulator_sum_reg <= {DATA_WIDTH{1'b0}};
        accepted_sample_count <= 32'd0;
      end else if (sample_valid && sample_ready) begin
        accumulator_sum_reg <= accumulator_sum_ext[DATA_WIDTH-1:0];
        accepted_sample_count <= accepted_sample_count + 32'd1;
      end
    end

    wire _unused_accumulator_sum_carry = accumulator_sum_ext[DATA_WIDTH];
    wire _unused_accepted_sample_count = ^accepted_sample_count;
  // SR2FPGA_BEHAVIOR_END
endmodule
