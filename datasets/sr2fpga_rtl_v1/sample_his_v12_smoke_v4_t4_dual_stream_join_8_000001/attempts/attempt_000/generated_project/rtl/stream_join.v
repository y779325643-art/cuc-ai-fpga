module stream_join #(
    parameter WIDTH = 8
) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] in0_data,
    input  wire in0_valid,
    output wire in0_ready,
    input  wire [WIDTH-1:0] in1_data,
    input  wire in1_valid,
    output wire in1_ready,
    output wire [WIDTH-1:0] out_data,
    output wire out_valid,
    input  wire out_ready
);

    assign in0_ready = in1_valid & out_ready;
    assign in1_ready = in0_valid & out_ready;
    assign out_valid = in0_valid & in1_valid;
    assign out_data = in0_data + in1_data;

endmodule
