module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [7:0] in_data,
    output wire [7:0] sum
);
    wire skid_out_valid;
    wire [7:0] skid_out_data;
    wire acc_sample_ready;
    wire skid_in_ready;

    skid_buffer #(.WIDTH(8)) skid (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .out_valid(skid_out_valid),
        .out_data(skid_out_data),
        .out_ready(acc_sample_ready),
        .in_ready(skid_in_ready)
    );

    accumulator_core #(.WIDTH(8)) acc (
        .clk(clk),
        .rst_n(rst_n),
        .sample_valid(skid_out_valid),
        .sample(skid_out_data),
        .sum(sum),
        .sample_ready(acc_sample_ready)
    );
endmodule
