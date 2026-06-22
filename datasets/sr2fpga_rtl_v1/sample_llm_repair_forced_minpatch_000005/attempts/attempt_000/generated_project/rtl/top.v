module top (
    input wire clk,
    input wire reset_n,
    input wire en,
    output reg [4:0] count
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 5'd0;
    end else if (en) begin
      count <= count + { 4'd0, 1'b1 };
    end
  end

endmodule
