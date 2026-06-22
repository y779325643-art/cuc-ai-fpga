module top (
    input wire clk,
    input wire reset_n,
    input wire en,
    output reg [3:0] count
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 4'd0;
    end else if (en) begin
      count <= count + { 3'd0, 1'b1 };
    end
  end

endmodule
