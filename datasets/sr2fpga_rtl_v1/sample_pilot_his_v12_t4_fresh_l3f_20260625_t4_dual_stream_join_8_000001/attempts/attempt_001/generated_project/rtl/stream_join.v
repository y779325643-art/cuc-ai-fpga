module stream_join #(parameter DATA_WIDTH=8) (
    input clk, rst_n,
    input in0_valid, output in0_ready,
    input [DATA_WIDTH-1:0] in0_data,
    input in1_valid, output in1_ready,
    output reg out_valid,
    input out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

reg sum_valid;
reg [DATA_WIDTH-1:0] sum_data;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        sum_valid <= 0;
        out_valid <= 0;
    end else begin
        if (out_ready && out_valid) begin
            sum_valid <= 0;
        end
        if (!sum_valid && in0_valid && in1_valid) begin
            sum_valid <= 1;
            sum_data <= in0_data + in1_data;
        end
        out_valid <= sum_valid;
        out_data <= sum_data;
    end
end

assign in0_ready = !sum_valid;
assign in1_ready = !sum_valid;

endmodule
