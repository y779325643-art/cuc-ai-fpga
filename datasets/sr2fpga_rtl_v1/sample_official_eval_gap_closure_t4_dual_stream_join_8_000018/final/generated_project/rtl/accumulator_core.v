module accumulator_core #(parameter SAMPLE_WIDTH = 16, parameter SUM_WIDTH = 9) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [SAMPLE_WIDTH-1:0] sample,
    output wire sample_ready,
    output wire sum_valid,
    output wire [SUM_WIDTH-1:0] sum,
    input wire sum_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [SUM_WIDTH-1:0] sum_reg;
    reg sum_valid_reg;
    assign sum = sum_reg;
    assign sum_valid = sum_valid_reg;
    assign sample_ready = !sum_valid_reg || sum_ready;
    always @(posedge clk) begin
      if (!rst_n) begin
        sum_reg <= 0;
        sum_valid_reg <= 0;
      end else begin
        if (sum_valid_reg && sum_ready) begin
          sum_valid_reg <= 0;
        end
        if (sample_valid && sample_ready) begin
          sum_reg <= sum_reg + sample[SUM_WIDTH-1:0];
          sum_valid_reg <= 1;
        end
      end
    end
endmodule
