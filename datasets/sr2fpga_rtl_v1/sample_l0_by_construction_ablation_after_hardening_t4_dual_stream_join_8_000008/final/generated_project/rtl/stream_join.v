module stream_join #(parameter DATA_WIDTH = 0) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [DATA_WIDTH-1:0] in0_data,
    output wire in0_ready,
    input wire in1_valid,
    input wire [DATA_WIDTH-1:0] in1_data,
    output wire in1_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
    localparam [1:0] IDLE = 2'd0;
    localparam [1:0] WAIT = 2'd1;
    localparam [1:0] JOINED = 2'd2;

    reg [1:0] state, next_state;
    reg [DATA_WIDTH-1:0] joined_data;

    assign in0_ready = (state == WAIT) && in0_valid && in1_valid;
    assign in1_ready = in0_ready;
    assign out_valid = (state == JOINED);
    assign out_data = joined_data;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        joined_data <= {DATA_WIDTH{1'b0}};
      end else begin
        state <= next_state;
        if (state == WAIT && in0_valid && in1_valid)
          joined_data <= in0_data;
      end
    end

    always @* begin
      next_state = state;
      case (state)
        IDLE: if (in0_valid || in1_valid) next_state = WAIT;
        WAIT: if (in0_valid && in1_valid) next_state = JOINED;
        JOINED: if (out_ready) next_state = IDLE;
        default: next_state = IDLE;
      endcase
    end
  localparam IDLE = 0;
  localparam WAIT = 0;
  localparam JOINED = 0;
endmodule
