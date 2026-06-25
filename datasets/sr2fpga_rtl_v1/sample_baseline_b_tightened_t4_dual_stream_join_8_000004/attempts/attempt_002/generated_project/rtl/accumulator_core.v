`timescale 1ns/1ns
module accumulator_core #(
    parameter DATA_WIDTH = 8,
    parameter SUM_WIDTH = 16
) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [2*DATA_WIDTH-1:0] sample,
    output wire sample_ready,
    output wire sum_valid,
    output wire [SUM_WIDTH-1:0] sum,
    input wire sum_ready
);

reg [SUM_WIDTH-1:0] acc;
reg valid;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        acc <= 0;
        valid <= 1'b0;
    end else begin
        if (sum_ready && valid) begin
            valid <= 1'b0;
        end
        if (sample_valid && !valid) begin
            acc <= acc + sample;
            valid <= 1'b1;
        end
    end
end

assign sample_ready = !valid;
assign sum_valid = valid;
assign sum = acc;

endmodule
