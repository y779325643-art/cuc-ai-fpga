module top (
    input clk,
    input rst_n,
    input in_valid,
    input [7:0] in_data,
    output reg [7:0] sum,
    output skid_ready
);

    wire skid_valid;
    wire [7:0] skid_data;
    wire acc_ready;

    skid_buffer u_skid (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .out_ready(acc_ready),
        .out_valid(skid_valid),
        .out_data(skid_data),
        .in_ready(skid_ready)
    );

    accumulator_core u_acc (
        .clk(clk),
        .rst_n(rst_n),
        .sample_valid(skid_valid),
        .sample(skid_data),
        .sample_ready(acc_ready),
        .sum(sum)
    );

endmodule
