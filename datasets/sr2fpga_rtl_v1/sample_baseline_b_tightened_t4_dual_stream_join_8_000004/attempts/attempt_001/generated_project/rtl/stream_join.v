`timescale 1ns/1ns
module stream_join #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [DATA_WIDTH-1:0] in0_data,
    output wire in0_ready,
    input wire in1_valid,
    input wire [DATA_WIDTH-1:0] in1_data,
    output wire in1_ready,
    output wire out_valid,
    output wire [2*DATA_WIDTH-1:0] out_data,
    input wire out_ready
);

reg join_valid;
reg [2*DATA_WIDTH-1:0] join_data;

assign in0_ready = !join_valid || out_ready;
assign in1_ready = !join_valid || out_ready;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        join_valid <= 1'b0;
    end else begin
        if (out_ready && join_valid) begin
            join_valid <= 1'b0;
        end
        if (in0_valid && in1_valid && !join_valid) begin
            join_valid <= 1'b1;
            join_data <= {in0_data, in1_data};
        end
    end
end

assign out_valid = join_valid;
assign out_data = join_data;

endmodule
