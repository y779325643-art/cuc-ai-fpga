module top #(
    parameter CLKS_PER_BIT = 4
) (
    input wire clk,
    input wire rst_n,
    input wire rx,
    output wire tx,
    input wire tx_enable
);

  wire [7:0] rx_data;
  wire rx_data_valid;
  wire rx_framing_error;
  wire [7:0] fifo_dout;
  wire fifo_full;
  wire fifo_empty;
  wire tx_busy;
  reg fifo_rd_en;
  reg tx_start;
  reg [7:0] tx_data;

  uart_rx_core #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_rx_core (
    .clk(clk),
    .rst_n(rst_n),
    .rx(rx),
    .data(rx_data),
    .data_valid(rx_data_valid),
    .framing_error(rx_framing_error)
  );

  sync_fifo_core u_sync_fifo_core (
    .clk(clk),
    .rst_n(rst_n),
    .wr_en(rx_data_valid && !fifo_full && !rx_framing_error && 1'b0),
    .din(rx_data),
    .rd_en(fifo_rd_en),
    .dout(fifo_dout),
    .full(fifo_full),
    .empty(fifo_empty)
  );

  uart_tx_core #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_tx_core (
    .clk(clk),
    .rst_n(rst_n),
    .start(tx_start),
    .data(tx_data),
    .tx(tx),
    .busy(tx_busy)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      fifo_rd_en <= 1'b0;
      tx_start <= 1'b0;
      tx_data <= 8'd0;
    end else begin
      fifo_rd_en <= 1'b0;
      tx_start <= 1'b0;
      if (tx_enable && !fifo_empty && !tx_busy && !tx_start) begin
        fifo_rd_en <= 1'b1;
        tx_start <= 1'b1;
        tx_data <= fifo_dout;
      end
    end
  end

endmodule
