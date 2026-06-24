module skid_buffer #(parameter W=8) (
    input clk, rst_n,
    input in_valid, input [W-1:0] in_data,
    output reg in_ready,
    output reg out_valid, output reg [W-1:0] out_data,
    input out_ready
);
    reg [W-1:0] buf_data;
    reg buf_valid;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_valid <= 0;
            buf_valid <= 0;
            in_ready <= 1;
        end else begin
            if (out_valid && out_ready) begin
                if (buf_valid) begin
                    out_data <= buf_data;
                    buf_valid <= 0;
                    in_ready <= 1;
                end else begin
                    out_valid <= 0;
                    in_ready <= 1;
                end
            end else if (!out_valid && in_valid) begin
                out_valid <= 1;
                out_data <= in_data;
                in_ready <= 1;
            end else if (out_valid && !out_ready && in_valid) begin
                buf_valid <= 1;
                buf_data <= in_data;
                in_ready <= 0;
            end
        end
    end
endmodule
