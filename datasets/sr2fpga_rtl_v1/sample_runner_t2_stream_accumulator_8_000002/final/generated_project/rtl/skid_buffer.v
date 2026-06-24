module skid_buffer (
    input clk,
    input rst_n,
    input in_valid,
    input [7:0] in_data,
    input out_ready,
    output reg out_valid,
    output reg [7:0] out_data,
    output reg in_ready
);

    reg [7:0] buf_data;
    reg buf_valid;
    wire bypass;

    assign bypass = in_valid & out_ready;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buf_valid <= 0;
            out_valid <= 0;
            out_data <= 0;
            in_ready <= 1;
            buf_data <= 0;
        end else begin
            if (bypass) begin
                out_valid <= in_valid;
                out_data <= in_data;
                buf_valid <= 0;
                in_ready <= 1;
            end else if (in_valid & in_ready & !out_ready) begin
                buf_valid <= 1;
                buf_data <= in_data;
                out_valid <= 0;
                in_ready <= 0;
            end else if (buf_valid & out_ready) begin
                out_valid <= 1;
                out_data <= buf_data;
                buf_valid <= 0;
                in_ready <= 1;
            end else begin
                if (out_ready & buf_valid) begin
                    out_valid <= 1;
                    out_data <= buf_data;
                    buf_valid <= 0;
                    in_ready <= 1;
                end else if (!in_valid) begin
                    out_valid <= 0;
                    in_ready <= 1;
                end
            end
        end
    end

endmodule
