module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    output wire sample_ready,
    input wire [DATA_WIDTH-1:0] sample,
    output wire sum_valid,
    input wire sum_ready,
    output wire [DATA_WIDTH-1:0] sum
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [DATA_WIDTH-1:0] sum_reg;
    reg sum_valid_reg;

    assign sample_ready = !sum_valid_reg || sum_ready;
    assign sum_valid = sum_valid_reg;
    assign sum = sum_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        sum_reg <= {DATA_WIDTH{1'b0}};
        sum_valid_reg <= 1'b0;
      end else begin
        if (sample_valid && sample_ready) begin
          sum_reg <= sum_reg + sample;
          sum_valid_reg <= 1'b1;
        end else if (sum_ready && sum_valid_reg) begin
          sum_valid_reg <= 1'b0;
        end
      end
    end
endmodule
