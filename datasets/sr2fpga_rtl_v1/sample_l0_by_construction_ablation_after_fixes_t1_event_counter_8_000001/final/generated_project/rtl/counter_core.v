module counter_core (
    input clk,
    input reset_n,
    input en,
    output reg [7:0] count
);
always @(posedge clk or negedge reset_n) begin
    if (!reset_n) count <= 8'd0;
    else if (en) count <= count + 1;
end
endmodule
