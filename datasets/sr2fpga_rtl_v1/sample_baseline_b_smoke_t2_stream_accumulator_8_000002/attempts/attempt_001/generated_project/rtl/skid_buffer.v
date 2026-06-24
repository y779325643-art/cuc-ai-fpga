module skid_buffer (
    input wire clk,
    input wire reset_n,
    input wire in_valid,
    input wire [7:0] in_data,
    input wire out_ready,
    output reg out_valid,
    output reg [7:0] out_data
);
    reg [7:0] buf_reg;
    reg has_buf;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            out_valid <= 1'b0;
            out_data <= 8'h0;
            buf_reg <= 8'h0;
            has_buf <= 1'b0;
        end else begin
            if (out_ready) begin
                if (has_buf) begin
                    out_valid <= 1'b1;
                    out_data <= buf_reg;
                    has_buf <= 1'b0;
                end else if (in_valid) begin
                    out_valid <= 1'b1;
                    out_data <= in_data;
                end else begin
                    out_valid <= 1'b0;
                    out_data <= 8'h0;
                end
            end else begin
                // out_ready low
                if (!has_buf && in_valid) begin
                    buf_reg <= in_data;
                    has_buf <= 1'b1;
                    out_valid <= 1'b0;
                    out_data <= 8'h0;
                end else begin
                    out_valid <= 1'b0;
                    out_data <= 8'h0;
                end
            end
        end
    end
endmodule
