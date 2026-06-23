module clock_divider #(parameter DIV = 100) (
    input clk,
    input rst_n,
    output reg sclk
);

reg [6:0] counter;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        counter <= 0;
        sclk <= 0;
    end else begin
        if (counter == DIV-1) begin
            counter <= 0;
            sclk <= ~sclk;
        end else begin
            counter <= counter + 1;
        end
    end
end

endmodule
