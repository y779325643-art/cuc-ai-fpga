module stream_join #(parameter DATA_WIDTH = 8) (
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] in0_data,
    input in0_valid,
    output reg in0_ready,
    input [DATA_WIDTH-1:0] in1_data,
    input in1_valid,
    output reg in1_ready,
    output reg [DATA_WIDTH-1:0] out_data,
    output reg out_valid,
    input out_ready
);

parameter IDLE = 2'd0, WAIT_BOTH = 2'd1, JOIN = 2'd2;
reg [1:0] state;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        out_valid <= 0;
        in0_ready <= 1;
        in1_ready <= 1;
    end else begin
        case (state)
            IDLE: begin
                in0_ready <= 1;
                in1_ready <= 1;
                if (in0_valid && in1_valid) begin
                    state <= JOIN;
                    out_data <= in0_data + in1_data;
                    out_valid <= 1;
                end else if (in0_valid || in1_valid) begin
                    state <= WAIT_BOTH;
                end
            end
            WAIT_BOTH: begin
                in0_ready <= 1;
                in1_ready <= 1;
                if (in0_valid && in1_valid) begin
                    state <= JOIN;
                    out_data <= in0_data + in1_data;
                    out_valid <= 1;
                end
            end
            JOIN: begin
                in0_ready <= 0;
                in1_ready <= 0;
                if (out_ready) begin
                    out_valid <= 0;
                    state <= IDLE;
                end
            end
        endcase
    end
end

endmodule
