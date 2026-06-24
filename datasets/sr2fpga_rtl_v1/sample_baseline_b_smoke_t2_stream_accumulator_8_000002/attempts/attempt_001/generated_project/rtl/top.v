module top (
    input wire clk,
    input wire reset_n,
    input wire in_valid,
    input wire [7:0] in_data,
    output wire [15:0] sum
);
    wire skid_out_valid;
    wire [7:0] skid_out_data;
    wire acc_sample_ready;
    skid_buffer u_skid (
        .clk(clk),
        .reset_n(reset_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .out_ready(acc_sample_ready),
        .out_valid(skid_out_valid),
        .out_data(skid_out_data)
    );
    accumulator_core u_acc (
        .clk(clk),
        .reset_n(reset_n),
        .sample_valid(skid_out_valid),
        .sample(skid_out_data),
        .sample_ready(acc_sample_ready),
        .sum(sum)
    );
endmodule
