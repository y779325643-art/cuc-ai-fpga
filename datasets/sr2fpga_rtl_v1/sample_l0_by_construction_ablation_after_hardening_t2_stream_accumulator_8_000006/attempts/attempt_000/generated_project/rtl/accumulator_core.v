module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [DATA_WIDTH-1:0] sample,
    output wire sample_ready,
    output wire [DATA_WIDTH-1:0] sum
);
    reg [DATA_WIDTH-1:0] accumulated_sum;
    reg                  sample_ready_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        accumulated_sum <= 0;
        sample_ready_reg <= 0;
      end else begin
        sample_ready_reg <= 1;                       // always ready after reset
        if (sample_valid && sample_ready_reg) begin
          accumulated_sum <= accumulated_sum + sample; // wraps on 8‑bit overflow
        end
      end
    end

    assign sample_ready = sample_ready_reg;
    assign sum          = accumulated_sum;
endmodule
