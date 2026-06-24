module counter_core #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire reset_n,
    input wire en,
    output reg [WIDTH-1:0] count
);

always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
        count <= 0;
    end else if (en) begin
        count <= count + 1;
    end
end

endmodule
