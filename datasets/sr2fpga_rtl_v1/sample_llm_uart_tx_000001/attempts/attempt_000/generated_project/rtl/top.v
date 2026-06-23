module top (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [7:0] data,
    output wire tx,
    output wire tx_busy
);
    wire baud_tick;
    baud_tick_gen #(
        .CLK_FREQ(100000000),
        .BAUD_RATE(115200)
    ) u_baud (
        .clk(clk),
        .rst_n(rst_n),
        .en(1'b1),
        .tick(baud_tick)
    );
    uart_tx_core u_uart (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .data(data),
        .baud_tick(baud_tick),
        .tx(tx),
        .busy(tx_busy)
    );
endmodule
