module accumulator_core #(parameter DATA_WIDTH = 0) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [DATA_WIDTH-1:0] sample_data,
    output wire sample_ready,
    output wire sum_valid,
    output wire [DATA_WIDTH-1:0] sum_data
);
    // Accumulator: always ready, maintains running sum
    reg [DATA_WIDTH-1:0] sum_reg;
    reg sum_valid_reg;

    assign sample_ready = 1'b1;
    assign sum_valid = sum_valid_reg;
    assign sum_data = sum_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        sum_reg <= {DATA_WIDTH{1'b0}};
        sum_valid_reg <= 1'b0;
      end else begin
        if (sample_valid && sample_ready) begin
          sum_reg <= sum_reg + sample_data;
          sum_valid_reg <= 1'b1;
        end
      end
    end
endmodule
