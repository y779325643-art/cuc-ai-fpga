module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [7:0] in_data,
    output wire out_ready,
    output wire [7:0] sum
);
    wire skid_out_valid;
    wire [7:0] skid_out_data;
    wire acc_sample_ready;
    skid_buffer #(.WIDTH(8)) skid_inst (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .out_ready(acc_sample_ready),
        .out_valid(skid_out_valid),
        .out_data(skid_out_data)
    );
    accumulator_core #(.WIDTH(8)) acc_inst (
        .clk(clk),
        .rst_n(rst_n),
        .sample_valid(skid_out_valid),
        .sample(skid_out_data),
        .sample_ready(acc_sample_ready),
        .sum(sum)
    );
    assign out_ready = acc_sample_ready;
endmodule
