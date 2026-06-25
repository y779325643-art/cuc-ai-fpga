module skid_buffer #(parameter WIDTH=8)(
    input clk,
    input rst_n,
    input in_valid,
    input [WIDTH-1:0] in_data,
    output reg out_valid,
    output reg [WIDTH-1:0] out_data,
    output in_ready,
    input out_ready
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        out_valid <= 0;
    end else if ((!out_valid || out_ready) && in_valid) begin
        out_valid <= 1;
        out_data <= in_data;
    end else if (out_ready) begin
        out_valid <= 0;
    end
end

assign in_ready = !out_valid || out_ready;

endmodule
