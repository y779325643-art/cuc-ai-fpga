module counter_core (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg [7:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'd0;
        end else if (en) begin
            count <= count + 1;
        end
    end
endmodule
