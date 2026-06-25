module accumulator_core #(parameter DATA_WIDTH = 8) (
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] in_data,
    input in_valid,
    output in_ready,
    output [DATA_WIDTH-1:0] out_data,
    output out_valid,
    input out_ready
);

reg [DATA_WIDTH-1:0] acc;

assign in_ready = out_ready;
assign out_valid = 1'b1;
assign out_data = acc;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        acc <= 0;
    end else if (in_valid && out_ready) begin
        acc <= acc + in_data;
    end
end

endmodule
