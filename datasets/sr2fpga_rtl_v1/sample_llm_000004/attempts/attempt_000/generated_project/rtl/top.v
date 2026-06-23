module top (
    input wire clk,
    input wire reset_n,
    input wire en,
    output reg [7:0] q
);

always @(posedge clk or negedge reset_n) begin
    if (!reset_n)
        q <= 8'b0;
    else if (en)
        q <= q + 1'b1;
end

endmodule
