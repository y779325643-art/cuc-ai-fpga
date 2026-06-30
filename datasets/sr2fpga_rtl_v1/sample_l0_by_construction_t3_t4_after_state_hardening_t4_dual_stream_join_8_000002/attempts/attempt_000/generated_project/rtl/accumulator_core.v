module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] sum,
    input wire out_ready
);
  module accumulator_core #(parameter DATA_WIDTH = 8) (
      input wire clk,
      input wire rst_n,
      input wire in_valid,
      input wire [DATA_WIDTH-1:0] in_data,
      output wire in_ready,
      output wire out_valid,
      output wire [DATA_WIDTH-1:0] sum,
      input wire out_ready
  );
    reg [DATA_WIDTH-1:0] acc_sum;
    reg out_valid_reg;

    assign sum = acc_sum;
    assign in_ready = !out_valid_reg || out_ready;
    assign out_valid = out_valid_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        acc_sum <= 0;
        out_valid_reg <= 1'b0;
      end else begin
        if (in_valid && in_ready) begin
          acc_sum <= acc_sum + in_data;
          out_valid_reg <= 1'b1;
        end
        if (out_ready && out_valid_reg) begin
          out_valid_reg <= 1'b0;
        end
      end
    end
  endmodule
endmodule
