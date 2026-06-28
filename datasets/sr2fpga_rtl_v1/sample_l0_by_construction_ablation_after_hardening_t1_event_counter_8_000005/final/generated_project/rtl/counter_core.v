module counter_core #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire en,
    output wire [WIDTH-1:0] count
);
  reg [WIDTH-1:0] value;
  assign count = value;
  always @(posedge clk) begin
      if (!rst_n)
          value <= 0;
      else if (en)
          value <= value + 1;
  end
endmodule
