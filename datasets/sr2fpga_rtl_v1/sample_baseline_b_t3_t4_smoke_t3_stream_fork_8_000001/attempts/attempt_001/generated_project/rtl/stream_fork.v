module stream_fork #(parameter WIDTH = 8) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] in_data,
    input in_valid,
    output reg in_ready,
    output reg [WIDTH-1:0] out0_data,
    output reg out0_valid,
    input out0_ready,
    output reg [WIDTH-1:0] out1_data,
    output reg out1_valid,
    input out1_ready
);

always @(*) begin
    in_ready = out0_ready && out1_ready;
    out0_data = in_data;
    out0_valid = in_valid;
    out1_data = in_data;
    out1_valid = in_valid;
end

endmodule
