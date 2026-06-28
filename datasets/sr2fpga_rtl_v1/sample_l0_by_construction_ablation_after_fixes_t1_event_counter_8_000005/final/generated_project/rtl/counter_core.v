module counter_core #(parameter WIDTH = 8) (
    input wire [1-1:0] clk,
    input wire [1-1:0] rst_n,
    input wire [1-1:0] en,
    output wire [WIDTH-1:0] count
);
    reg [WIDTH-1:0] count_reg;
    always @(posedge clk) begin
      if (!rst_n)
        count_reg <= {WIDTH{1'b0}};
      else if (en)
        count_reg <= count_reg + 1'b1;
    end
    assign count = count_reg;
endmodule
