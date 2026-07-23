module uart_tx_core (
    input wire clk,
    input wire rst_n,
    input wire baud_tick,
    input wire start,
    input wire [7:0] data,
    output reg tx,
    output reg busy,
    output reg done
);

  localparam [1:0] IDLE = 2'd0;
  localparam [1:0] DATA = 2'd1;
  localparam [1:0] STOP = 2'd2;
  localparam [1:0] CLEANUP = 2'd3;

  reg [1:0] state;
  reg [2:0] bit_index;
  reg [7:0] shifter;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      bit_index <= 3'd0;
      shifter <= 8'd0;
      tx <= 1'b1;
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      case (state)
        IDLE: begin
          tx <= 1'b1;
          busy <= 1'b0;
          bit_index <= 3'd0;
          if (start) begin
            shifter <= data;
            tx <= 1'b0;
            busy <= 1'b1;
            state <= DATA;
          end
        end
        DATA: begin
          if (baud_tick) begin
            tx <= shifter[0];
            shifter <= {1'b0, shifter[7:1]};
            if (bit_index == 3'd7) begin
              bit_index <= 3'd0;
              state <= STOP;
            end else begin
              bit_index <= bit_index + 3'd1;
            end
          end
        end
        STOP: begin
          if (baud_tick) begin
            tx <= 1'b0;
            state <= CLEANUP;
          end
        end
        CLEANUP: begin
          if (baud_tick) begin
            tx <= 1'b1;
            busy <= 1'b0;
            done <= 1'b1;
            state <= IDLE;
          end
        end
        default: begin
          state <= IDLE;
          tx <= 1'b1;
          busy <= 1'b0;
        end
      endcase
    end
  end

endmodule
