module top (
    input wire clk,
    input wire rst_n,
    input wire start,
    output reg done,
    output reg [7:0] state_value
);

  localparam [1:0] IDLE = 2'd0;
  localparam [1:0] RUN = 2'd1;
  localparam [1:0] DONE = 2'd2;

  reg [1:0] state;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      done <= 1'b0;
      state_value <= 8'd0;
    end else begin
      case (state)
        IDLE: begin
          done <= 1'b0;
          state_value <= 8'd0;
          if (start) begin
            state <= RUN;
          end
        end
        RUN: begin
          state_value <= state_value + { 7'd0, 1'b1 };
          if (state_value == 8'd2) begin
            state <= DONE;
          end
        end
        DONE: begin
          done <= 1'b1;
          if (!start) begin
            state <= IDLE;
          end
        end
        default: begin
          state <= IDLE;
        end
      endcase
    end
  end

endmodule
