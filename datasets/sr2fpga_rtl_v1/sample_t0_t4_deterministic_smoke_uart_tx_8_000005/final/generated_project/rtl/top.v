module top (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [7:0] data,
    output wire tx,
    output wire busy,
    output wire done
);

  wire baud_tick;

  baud_tick_gen u_baud_tick_gen (
    .clk(clk),
    .rst_n(rst_n),
    .enable(busy),
    .tick(baud_tick)
  );

  uart_tx_core u_uart_tx_core (
    .clk(clk),
    .rst_n(rst_n),
    .baud_tick(baud_tick),
    .start(start),
    .data(data),
    .tx(tx),
    .busy(busy),
    .done(done)
  );

endmodule
