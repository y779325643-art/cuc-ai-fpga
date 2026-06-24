`timescale 1ns/1ns
module stream_stage #(
    parameter DATA_WIDTH = 16
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

reg pipe_valid;
reg [DATA_WIDTH-1:0] pipe_data;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pipe_valid <= 1'b0;
    end else begin
        if (out_ready && pipe_valid) begin
            pipe_valid <= 1'b0;
        end
        if (in_valid && (!pipe_valid || out_ready)) begin
            pipe_data <= in_data;
            pipe_valid <= 1'b1;
        end
    end
end

assign in_ready = !pipe_valid || out_ready;
assign out_valid = pipe_valid;
assign out_data = pipe_data;

endmodule
