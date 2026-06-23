module top (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg [7:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'b0;
        else if (en)
            count <= count + 1'b1;
    end
endmodule