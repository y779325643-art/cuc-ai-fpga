module top (
    input clk,
    input rst_n,
    output reg [1:0] state,
    output reg out
);

// state encoding
localparam S0 = 2'b00,
           S1 = 2'b01,
           S2 = 2'b10,
           S3 = 2'b11;

reg [1:0] next_state;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        state <= S0;
    else
        state <= next_state;
end

always @(*) begin
    case (state)
        S0: next_state = S1;
        S1: next_state = S2;
        S2: next_state = S3;
        S3: next_state = S0;
        default: next_state = S0;
    endcase
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        out <= 1'b0;
    else if (state == S3)
        out <= 1'b1;
    else
        out <= 1'b0;
end

endmodule
