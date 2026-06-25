module skid_buffer #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [WIDTH-1:0] out_data,
    input wire out_ready
);

reg [WIDTH-1:0] buf_data;
reg buf_valid;
reg bypass;
wire accept_in;

assign accept_in = (!buf_valid || (out_ready && bypass)) && (!bypass || out_ready);
assign in_ready = !buf_valid || (out_ready && bypass);
assign out_valid = buf_valid || (in_valid && !bypass);
assign out_data = bypass ? in_data : buf_data;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        buf_valid <= 1'b0;
        bypass <= 1'b0;
    end else begin
        if (in_valid && accept_in) begin
            if (out_ready && bypass) begin
                bypass <= 1'b0;
            end else if (buf_valid && out_ready) begin
                buf_data <= in_data;
            end else begin
                buf_data <= in_data;
                buf_valid <= 1'b1;
                bypass <= 1'b0;
            end
        end else if (buf_valid && out_ready) begin
            buf_valid <= 1'b0;
        end
        // bypass logic
        if (in_valid && !buf_valid) begin
            bypass <= 1'b1;
        end else if (out_ready && bypass) begin
            bypass <= 1'b0;
        end
    end
end

endmodule
