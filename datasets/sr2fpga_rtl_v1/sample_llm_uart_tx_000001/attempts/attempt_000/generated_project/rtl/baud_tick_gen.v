module baud_tick_gen #(
    parameter CLK_FREQ = 100000000,
    parameter BAUD_RATE = 115200
) (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg tick
);
    localparam DIVISOR = CLK_FREQ / BAUD_RATE;
    reg [15:0] counter;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 0;
            tick <= 0;
        end else if (en) begin
            if (counter == DIVISOR - 1) begin
                counter <= 0;
                tick <= 1;
            end else begin
                counter <= counter + 1;
                tick <= 0;
            end
        end else begin
            counter <= 0;
            tick <= 0;
        end
    end
endmodule
