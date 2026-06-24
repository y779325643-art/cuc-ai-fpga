module stream_fork #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out0_valid,
    input wire out0_ready,
    output wire [WIDTH-1:0] out0_data,
    output wire out1_valid,
    input wire out1_ready,
    output wire [WIDTH-1:0] out1_data
);

    assign in_ready = out0_ready && out1_ready;
    assign out0_valid = in_valid;
    assign out0_data = in_data;
    assign out1_valid = in_valid;
    assign out1_data = in_data;

endmodule
