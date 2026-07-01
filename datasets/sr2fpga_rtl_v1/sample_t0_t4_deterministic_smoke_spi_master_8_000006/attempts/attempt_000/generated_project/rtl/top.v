module top (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [7:0] tx_data,
    input wire miso,
    output wire [7:0] rx_data,
    output wire busy,
    output wire done,
    output wire sclk,
    output wire mosi,
    output wire cs_n
);

  wire spi_tick;

  clock_divider u_clock_divider (
    .clk(clk),
    .rst_n(rst_n),
    .enable(busy),
    .tick(spi_tick)
  );

  spi_master_core u_spi_master_core (
    .clk(clk),
    .rst_n(rst_n),
    .tick(spi_tick),
    .start(start),
    .tx_data(tx_data),
    .miso(miso),
    .rx_data(rx_data),
    .busy(busy),
    .done(done),
    .sclk(sclk),
    .mosi(mosi),
    .cs_n(cs_n)
  );

endmodule
