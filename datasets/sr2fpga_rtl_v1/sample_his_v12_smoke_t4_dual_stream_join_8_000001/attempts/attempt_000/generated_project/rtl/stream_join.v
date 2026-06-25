module stream_join #(
    parameter DATA_WIDTH = 8
) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire [DATA_WIDTH-1:0] data_in0,
    input  wire                  valid_in0,
    output reg                   ready_out0,
    input  wire [DATA_WIDTH-1:0] data_in1,
    input  wire                  valid_in1,
    output reg                   ready_out1,
    output reg  [DATA_WIDTH-1:0] data_out,
    output reg                   valid_out,
    input  wire                  ready_in
);

localparam IDLE = 2'd0;
localparam WAIT_BOTH = 2'd1;
localparam OUTPUT = 2'd2;

reg [1:0] state;
reg [1:0] next_state;

// State registers
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
    end else begin
        state <= next_state;
    end
end

// Next state logic and output
always @(*) begin
    next_state = state;
    ready_out0 = 1'b0;
    ready_out1 = 1'b0;
    data_out = {DATA_WIDTH{1'b0}};
    valid_out = 1'b0;
    case (state)
        IDLE: begin
            ready_out0 = 1'b1;
            ready_out1 = 1'b1;
            if (valid_in0 || valid_in1) begin
                next_state = WAIT_BOTH;
            end
        end
        WAIT_BOTH: begin
            ready_out0 = 1'b1;
            ready_out1 = 1'b1;
            if (valid_in0 && valid_in1) begin
                next_state = OUTPUT;
            end
        end
        OUTPUT: begin
            if (ready_in) begin
                data_out = data_in0 + data_in1;
                valid_out = 1'b1;
                next_state = IDLE;
            end else begin
                // hold output until ready
                data_out = data_in0 + data_in1;
                valid_out = 1'b1;
                ready_out0 = 1'b0;
                ready_out1 = 1'b0;
            end
        end
        default: next_state = IDLE;
    endcase
end

endmodule
