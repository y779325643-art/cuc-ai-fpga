module skid_buffer #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [WIDTH-1:0] out_data
);

    reg [WIDTH-1:0] buffer_data;
    reg buffer_valid;
    reg bypass;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buffer_valid <= 1'b0;
            bypass <= 1'b0;
        end else begin
            if (in_valid && in_ready) begin
                buffer_data <= in_data;
                buffer_valid <= 1'b1;
            end else if (out_ready || !out_valid) begin
                buffer_valid <= 1'b0;
            end
            if (out_valid && out_ready) begin
                bypass <= 1'b0;
            end else if (in_valid && out_valid && !out_ready) begin
                bypass <= 1'b1;
            end
        end
    end

    assign in_ready = !buffer_valid || (out_ready && !bypass);
    assign out_valid = bypass ? 1'b1 : (buffer_valid || in_valid);
    assign out_data = bypass ? in_data : (buffer_valid ? buffer_data : in_data);

endmodule
