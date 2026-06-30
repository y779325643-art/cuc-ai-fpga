module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [DATA_WIDTH-1:0] sample,
    input wire sample_ready,
    output wire [DATA_WIDTH-1:0] sum
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [DATA_WIDTH-1:0] accum_sum;

    assign sum = accum_sum;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        accum_sum <= {DATA_WIDTH{1'b0}};
      end else begin
        if (sample_valid && sample_ready) begin
          accum_sum <= accum_sum + sample;
        end
      end
    end
endmodule
