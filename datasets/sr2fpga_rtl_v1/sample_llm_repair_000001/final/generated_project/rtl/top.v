module top (
    input clk,
    input rst_n,
    input en,
    output reg [7:0] count
);
always @(posedge clk or negedge rst_n)
    if (!rst_n) count <= 8'b0;
    else if (en) count <= count + 1'b1;
endmodule
