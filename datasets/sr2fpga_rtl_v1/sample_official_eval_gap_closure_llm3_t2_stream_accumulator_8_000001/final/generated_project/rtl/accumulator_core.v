module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid_in,
    input wire [DATA_WIDTH-1:0] sample,
    output wire sample_ready,
    output wire [DATA_WIDTH-1:0] sum,
    output wire sample_valid
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [DATA_WIDTH-1:0] sum_reg;

    assign sample_ready = 1'b1;
    assign sum = sum_reg;
    assign sample_valid = sample_valid_in;

    always @(posedge clk) begin
      if (!rst_n) begin
        sum_reg <= 0;
      end else begin
        if (sample_valid_in) begin
          sum_reg <= sum_reg + sample;
        end
      end
    end
endmodule
