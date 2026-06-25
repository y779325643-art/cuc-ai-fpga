module stream_stage #(parameter DATA_WIDTH = 8) (
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] in_data,
    input in_valid,
    output in_ready,
    output reg [DATA_WIDTH-1:0] out_data,
    output reg out_valid,
    input out_ready
);

reg [DATA_WIDTH-1:0] data_reg;
reg valid_reg;

assign in_ready = !valid_reg || (valid_reg && out_ready);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        valid_reg <= 0;
    end else begin
        if (in_valid && (out_ready || !valid_reg)) begin
            data_reg <= in_data;
            valid_reg <= 1;
        end else if (out_ready && valid_reg) begin
            valid_reg <= 0;
        end
    end
end

assign out_data = data_reg;
assign out_valid = valid_reg;

endmodule
