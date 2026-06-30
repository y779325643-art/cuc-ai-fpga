module top (
    input         clk,
    input         rst_n,
    input         in_valid,
    input  [7:0]  in_data,
    output [7:0]  sum
);
    wire sample_valid;
    wire [7:0] sample;
    wire sample_ready;

    skid_buffer #(.DATA_WIDTH(8)) u_skid (
        .clk       (clk),
        .rst_n     (rst_n),
        .in_valid  (in_valid),
        .in_data   (in_data),
        .in_ready  (),
        .out_valid (sample_valid),
        .out_data  (sample),
        .out_ready (sample_ready)
    );

    accumulator_core #(.DATA_WIDTH(8)) u_acc (
        .clk           (clk),
        .rst_n         (rst_n),
        .sample_valid  (sample_valid),
        .sample        (sample),
        .sample_ready  (sample_ready),
        .sum           (sum)
    );
endmodule
