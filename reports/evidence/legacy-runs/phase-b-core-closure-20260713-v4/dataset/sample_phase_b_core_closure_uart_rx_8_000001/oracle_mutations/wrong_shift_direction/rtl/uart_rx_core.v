module uart_rx_core #(
    parameter CLKS_PER_BIT = 4
) (
    input wire clk,
    input wire rst_n,
    input wire rx,
    output reg [7:0] data,
    output reg data_valid,
    output reg framing_error
);

  localparam [15:0] CLKS_PER_BIT_16 = CLKS_PER_BIT;
  localparam [15:0] HALF_CLKS_PER_BIT = CLKS_PER_BIT_16 / 2;
  localparam [1:0] IDLE = 2'd0;
  localparam [1:0] START = 2'd1;
  localparam [1:0] DATA = 2'd2;
  localparam [1:0] STOP = 2'd3;

  reg [1:0] state;
  reg [15:0] sample_count;
  reg [2:0] bit_index;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      sample_count <= 16'd0;
      bit_index <= 3'd0;
      data <= 8'd0;
      data_valid <= 1'b0;
      framing_error <= 1'b0;
    end else begin
      data_valid <= 1'b0;
      framing_error <= 1'b0;
      case (state)
        IDLE: begin
          sample_count <= 16'd0;
          bit_index <= 3'd0;
          if (!rx)
            state <= START;
        end
        START: begin
          if (sample_count == HALF_CLKS_PER_BIT - 16'd1) begin
            sample_count <= 16'd0;
            if (!rx) begin
              bit_index <= 3'd0;
              state <= DATA;
            end else begin
              state <= IDLE;
            end
          end else begin
            sample_count <= sample_count + 16'd1;
          end
        end
        DATA: begin
          if (sample_count == CLKS_PER_BIT_16 - 16'd1) begin
            sample_count <= 16'd0;
            data[3'd7 - bit_index] <= rx;
            if (bit_index == 3'd7)
              state <= STOP;
            else
              bit_index <= bit_index + 3'd1;
          end else begin
            sample_count <= sample_count + 16'd1;
          end
        end
        STOP: begin
          if (sample_count == CLKS_PER_BIT_16 - 16'd1) begin
            sample_count <= 16'd0;
            state <= IDLE;
            if (rx)
              data_valid <= 1'b1;
            else
              framing_error <= 1'b1;
          end else begin
            sample_count <= sample_count + 16'd1;
          end
        end
        default: begin
          state <= IDLE;
        end
      endcase
    end
  end

endmodule
