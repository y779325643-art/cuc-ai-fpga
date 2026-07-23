module top #(
    parameter CLKS_PER_BIT = 4
) (
    input wire clk,
    input wire rst_n,
    input wire rx,
    output wire [7:0] data,
    output wire data_valid,
    output wire framing_error
);

  uart_rx_core #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_rx_core (
    .clk(clk),
    .rst_n(rst_n),
    .rx(rx),
    .data(data),
    .data_valid(data_valid),
    .framing_error(framing_error)
  );

endmodule
