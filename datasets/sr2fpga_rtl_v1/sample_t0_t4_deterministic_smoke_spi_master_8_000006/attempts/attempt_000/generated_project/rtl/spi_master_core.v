module spi_master_core (
    input wire clk,
    input wire rst_n,
    input wire tick,
    input wire start,
    input wire [7:0] tx_data,
    input wire miso,
    output reg [7:0] rx_data,
    output reg busy,
    output reg done,
    output reg sclk,
    output reg mosi,
    output reg cs_n
);

  reg [2:0] bit_index;
  reg [7:0] tx_shift;
  reg [6:0] rx_shift;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      bit_index <= 3'd0;
      tx_shift <= 8'd0;
      rx_shift <= 7'd0;
      rx_data <= 8'd0;
      busy <= 1'b0;
      done <= 1'b0;
      sclk <= 1'b0;
      mosi <= 1'b0;
      cs_n <= 1'b1;
    end else begin
      done <= 1'b0;
      if (!busy) begin
        sclk <= 1'b0;
        cs_n <= 1'b1;
        bit_index <= 3'd0;
        if (start) begin
          busy <= 1'b1;
          cs_n <= 1'b0;
          tx_shift <= {tx_data[6:0], 1'b0};
          rx_shift <= 7'd0;
          mosi <= tx_data[7];
        end
      end else if (tick) begin
        if (sclk == 1'b0) begin
          sclk <= 1'b1;
          rx_shift <= {rx_shift[5:0], miso};
          if (bit_index == 3'd7) begin
            rx_data <= {rx_shift, miso};
          end
        end else begin
          sclk <= 1'b0;
          if (bit_index == 3'd7) begin
            busy <= 1'b0;
            done <= 1'b1;
            cs_n <= 1'b1;
          end else begin
            bit_index <= bit_index + 3'd1;
            mosi <= tx_shift[7];
            tx_shift <= {tx_shift[6:0], 1'b0};
          end
        end
      end
    end
  end

endmodule
