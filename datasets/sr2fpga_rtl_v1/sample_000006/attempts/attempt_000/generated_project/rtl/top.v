module top (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg [23:0] count
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 24'd0;
    end else if (en) begin
      count <= count + { 23'd0, 1'b1 };
    end
  end

endmodule
