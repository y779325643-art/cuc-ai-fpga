module accumulator_core #(parameter W=8) (
    input clk, rst_n,
    input sample_valid, input [W-1:0] sample,
    output reg sample_ready,
    output reg sum_valid, output reg [W-1:0] sum,
    input sum_ready
);
    reg [W-1:0] acc;
    reg state;
    localparam IDLE = 0, HOLD = 1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc <= 0;
            sum_valid <= 0;
            sample_ready <= 1;
            state <= IDLE;
        end else begin
            case(state)
                IDLE: begin
                    sample_ready <= 1;
                    if (sample_valid) begin
                        acc <= acc + sample;
                        sum <= acc + sample;
                        sum_valid <= 1;
                        state <= HOLD;
                        sample_ready <= 0;
                    end else begin
                        sum_valid <= 0;
                    end
                end
                HOLD: begin
                    sample_ready <= 0;
                    if (sum_ready) begin
                        state <= IDLE;
                        sum_valid <= 0;
                    end
                end
            endcase
        end
    end
endmodule
