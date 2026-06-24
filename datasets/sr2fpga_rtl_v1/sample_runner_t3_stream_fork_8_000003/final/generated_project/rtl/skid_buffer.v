module skid_buffer #(parameter WIDTH=8) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] in_data,
    input in_valid,
    output reg in_ready,
    output reg out_valid,
    output reg [WIDTH-1:0] out_data,
    input out_ready
);
    reg [WIDTH-1:0] buf_data;
    reg buf_valid;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_valid <= 0;
            buf_valid <= 0;
            out_data <= 0;
            buf_data <= 0;
        end else begin
            if (out_ready && out_valid) begin
                out_valid <= 0;
            end
            if (buf_valid && !out_valid) begin
                out_valid <= 1;
                out_data <= buf_data;
                buf_valid <= 0;
            end
            if (in_valid && in_ready) begin
                if (!out_valid) begin
                    out_valid <= 1;
                    out_data <= in_data;
                end else begin
                    if (!buf_valid) begin
                        buf_valid <= 1;
                        buf_data <= in_data;
                    end
                end
            end
        end
    end
    assign in_ready = !buf_valid && (!out_valid || out_ready);
endmodule
