module counter_core #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire en,
    output wire [WIDTH-1:0] count
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [WIDTH-1:0] count_reg;
    assign count = count_reg;
    always @(posedge clk) begin
      if (!rst_n) begin
        count_reg <= 0;
      end else if (en) begin
        count_reg <= count_reg + 1;
      end
    end
endmodule
