module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    output wire sample_ready,
    input wire [DATA_WIDTH-1:0] sample,
    output wire [DATA_WIDTH-1:0] sum
);
    reg [DATA_WIDTH-1:0] sum_reg;
    assign sum = sample_valid ? (sum_reg + sample) : sum_reg;
    assign sample_ready = 1'b1;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        sum_reg <= 0;
      end else if (sample_valid && sample_ready) begin
        sum_reg <= sum_reg + sample;
      end
    end
endmodule
