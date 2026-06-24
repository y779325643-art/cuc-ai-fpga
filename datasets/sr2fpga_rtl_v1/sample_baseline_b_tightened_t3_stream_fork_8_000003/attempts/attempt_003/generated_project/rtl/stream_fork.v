module stream_fork #(parameter WIDTH=8)(
    input clk,
    input rst_n,
    input in_valid,
    input [WIDTH-1:0] in_data,
    output reg out0_valid,
    output reg [WIDTH-1:0] out0_data,
    output reg out1_valid,
    output reg [WIDTH-1:0] out1_data,
    output in_ready,
    input out0_ready,
    input out1_ready
);

reg held_valid;
reg [WIDTH-1:0] held_data;

wire both_ready = (out0_ready || !out0_valid) && (out1_ready || !out1_valid);
assign in_ready = both_ready;  // only accept when both downstream can accept

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        out0_valid <= 0;
        out1_valid <= 0;
        held_valid <= 0;
    end else begin
        if (both_ready) begin
            if (in_valid) begin
                out0_valid <= 1;
                out0_data <= in_data;
                out1_valid <= 1;
                out1_data <= in_data;
                held_valid <= 0;
            end else begin
                out0_valid <= 0;
                out1_valid <= 0;
                held_valid <= 0;
            end
        end else begin
            // Hold state
            if (in_valid && !both_ready) begin
                held_valid <= 1;
                held_data <= in_data;
            end
            if (out0_ready && out0_valid) out0_valid <= 0;
            if (out1_ready && out1_valid) out1_valid <= 0;
        end
        // Output held data when both ready
        if (held_valid && both_ready) begin
            out0_valid <= 1;
            out0_data <= held_data;
            out1_valid <= 1;
            out1_data <= held_data;
            held_valid <= 0;
        end
    end
end

endmodule
