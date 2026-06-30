module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    output wire sample_ready,
    input wire [DATA_WIDTH-1:0] sample,
    output wire [DATA_WIDTH-1:0] sum
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [DATA_WIDTH-1:0] sum_reg;

    assign sample_ready = 1'b1;
    assign sum = sum_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            sum_reg <= {DATA_WIDTH{1'b0}};
        end else if (sample_valid) begin
            sum_reg <= sum_reg + sample;
        end
    end
endmodule
