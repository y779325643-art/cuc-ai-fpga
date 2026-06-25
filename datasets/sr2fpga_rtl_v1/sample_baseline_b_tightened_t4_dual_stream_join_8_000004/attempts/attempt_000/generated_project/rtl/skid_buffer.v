`timescale 1ns/1ns
module skid_buffer #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);

reg buffer_valid;
reg [DATA_WIDTH-1:0] buffer_data;
reg bypass;

wire fifo_full;
assign fifo_full = buffer_valid;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        buffer_valid <= 1'b0;
        bypass <= 1'b0;
    end else begin
        if (out_ready && buffer_valid) begin
            buffer_valid <= 1'b0;
        end
        if (in_valid && (in_ready || bypass)) begin
            if (out_ready && !buffer_valid) begin
                // direct bypass
                bypass <= 1'b1;
            end else begin
                buffer_data <= in_data;
                buffer_valid <= 1'b1;
                bypass <= 1'b0;
            end
        end else if (in_valid && in_ready && out_ready && buffer_valid) begin
            // when buffer is full but both ready, we can bypass
            bypass <= 1'b1;
        end else if (bypass && out_ready) begin
            bypass <= 1'b0;
        end
    end
end

assign in_ready = !fifo_full || (out_ready && !bypass);
assign out_valid = bypass || buffer_valid;
assign out_data = bypass ? in_data : buffer_data;

endmodule
