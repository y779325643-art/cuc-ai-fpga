module top (
    input clk,
    input rst_n,
    output reg [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n)
            count <= 6'd0;
        else
            count <= count + 1'd1;
    end
endmodule
