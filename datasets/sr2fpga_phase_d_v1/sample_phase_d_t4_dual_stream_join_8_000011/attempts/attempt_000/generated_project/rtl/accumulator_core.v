module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [DATA_WIDTH-1:0] sample_data,
    output wire sample_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] accumulator_value_reg;
    reg [DATA_WIDTH-1:0] next_accumulator_value;
    reg out_valid_reg;
    reg [DATA_WIDTH-1:0] out_data_reg;

    always @(*) begin
      next_accumulator_value = accumulator_value_reg + sample_data;
    end

    always @(posedge clk) begin
      if (!rst_n) begin
        accumulator_value_reg <= {DATA_WIDTH{1'b0}};
        out_valid_reg <= 1'b0;
        out_data_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        if (sample_valid && sample_ready) begin
          accumulator_value_reg <= next_accumulator_value;
        end
        if (sample_valid && sample_ready) begin
          out_valid_reg <= 1'b1;
          out_data_reg <= next_accumulator_value;
        end else if (out_ready) begin
          out_valid_reg <= 1'b0;
        end
      end
    end

    assign sample_ready = 1'b1;
    assign out_valid = out_valid_reg;
    assign out_data = out_data_reg;
  // SR2FPGA_BEHAVIOR_END
endmodule
