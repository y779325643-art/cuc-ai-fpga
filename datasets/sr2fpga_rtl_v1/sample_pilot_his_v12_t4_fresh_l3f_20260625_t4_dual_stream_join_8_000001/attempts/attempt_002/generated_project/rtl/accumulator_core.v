module accumulator_core #(parameter DATA_WIDTH=8) (
    input clk, rst_n,
    input in_valid,
    output in_ready,
    input [DATA_WIDTH-1:0] in_data,
    output reg out_valid,
    input out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

reg acc_valid;
reg [DATA_WIDTH-1:0] acc_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        acc_valid <= 0;
        out_valid <= 0;
        acc_reg <= 0;
    end else begin
        if (out_ready && out_valid) begin
            acc_valid <= 0;
        end
        if (in_valid && out_ready) begin
            acc_valid <= 1;
            acc_reg <= in_data;
        end
        out_valid <= acc_valid;
        out_data <= acc_reg;
    end
end

assign in_ready = out_ready;

endmodule
