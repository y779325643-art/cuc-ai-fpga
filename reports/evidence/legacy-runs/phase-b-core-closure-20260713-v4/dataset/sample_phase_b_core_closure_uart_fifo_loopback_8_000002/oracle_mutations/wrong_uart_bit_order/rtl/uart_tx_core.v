module uart_tx_core #(
    parameter CLKS_PER_BIT = 4
) (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [7:0] data,
    output reg tx,
    output reg busy
);

  localparam [15:0] CLKS_PER_BIT_16 = CLKS_PER_BIT;
  localparam [1:0] IDLE = 2'd0;
  localparam [1:0] START = 2'd1;
  localparam [1:0] DATA = 2'd2;
  localparam [1:0] STOP = 2'd3;

  reg [1:0] state;
  reg [15:0] bit_count;
  reg [2:0] bit_index;
  reg [7:0] shifter;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      bit_count <= 16'd0;
      bit_index <= 3'd0;
      shifter <= 8'd0;
      tx <= 1'b1;
      busy <= 1'b0;
    end else begin
      case (state)
        IDLE: begin
          tx <= 1'b1;
          busy <= 1'b0;
          bit_count <= 16'd0;
          if (start) begin
            shifter <= data;
            tx <= 1'b0;
            busy <= 1'b1;
            state <= START;
          end
        end
        START: begin
          if (bit_count == CLKS_PER_BIT_16 - 16'd1) begin
            bit_count <= 16'd0;
            bit_index <= 3'd0;
            tx <= shifter[7];
            state <= DATA;
          end else begin
            bit_count <= bit_count + 16'd1;
          end
        end
        DATA: begin
          if (bit_count == CLKS_PER_BIT_16 - 16'd1) begin
            bit_count <= 16'd0;
            if (bit_index == 3'd7) begin
              tx <= 1'b1;
              state <= STOP;
            end else begin
              bit_index <= bit_index + 3'd1;
              tx <= shifter[3'd6 - bit_index];
            end
          end else begin
            bit_count <= bit_count + 16'd1;
          end
        end
        STOP: begin
          if (bit_count == CLKS_PER_BIT_16 - 16'd1) begin
            bit_count <= 16'd0;
            busy <= 1'b0;
            tx <= 1'b1;
            state <= IDLE;
          end else begin
            bit_count <= bit_count + 16'd1;
          end
        end
        default: begin
          state <= IDLE;
        end
      endcase
    end
  end

endmodule
