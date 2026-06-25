module stream_join #(parameter W = 8) (
  input clk, reset_n,
  input valid0,
  input [W-1:0] data0,
  output ready0,
  input valid1,
  input [W-1:0] data1,
  output ready1,
  output valid_out,
  output [W-1:0] data_out,
  input ready_in
);

parameter [1:0] IDLE = 2'b00, WAIT0 = 2'b01, WAIT1 = 2'b10, JOIN = 2'b11;

reg [1:0] state;
reg [W-1:0] buf_data0, buf_data1;

wire [W-1:0] sum = buf_data0 + buf_data1;

always @(posedge clk or negedge reset_n) begin
  if (!reset_n) begin
    state <= IDLE;
    buf_data0 <= 0;
    buf_data1 <= 0;
  end else begin
    case (state)
      IDLE: begin
        if (valid0 && valid1 && ready_in) begin
          buf_data0 <= data0;
          buf_data1 <= data1;
          state <= JOIN;
        end else if (valid0) begin
          buf_data0 <= data0;
          state <= WAIT1;
        end else if (valid1) begin
          buf_data1 <= data1;
          state <= WAIT0;
        end
      end
      WAIT0: begin
        if (valid0 && ready_in) begin
          buf_data0 <= data0;
          state <= JOIN;
        end
      end
      WAIT1: begin
        if (valid1 && ready_in) begin
          buf_data1 <= data1;
          state <= JOIN;
        end
      end
      JOIN: begin
        if (ready_in) begin
          state <= IDLE;
        end
      end
    endcase
  end
end

assign ready0 = (state == IDLE) || (state == WAIT0);
assign ready1 = (state == IDLE) || (state == WAIT1);
assign valid_out = (state == JOIN);
assign data_out = sum;

endmodule
