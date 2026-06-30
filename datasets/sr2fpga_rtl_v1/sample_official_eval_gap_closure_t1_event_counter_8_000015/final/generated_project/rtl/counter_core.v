module counter_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire en,
    output wire [DATA_WIDTH-1:0] count
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [DATA_WIDTH-1:0] count_reg;
    assign count = count_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        count_reg <= {DATA_WIDTH{1'b0}};
      end else if (en) begin
        count_reg <= count_reg + 1'b1;
      end
    end
endmodule
