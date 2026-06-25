// Accumulator that adds input data to internal register on each valid transfer
`timescale 1ns / 1ps

module accumulator_core #(
    parameter DATA_WIDTH = 8
) (
    input  wire                        clk,
    input  wire                        reset_n,
    input  wire [DATA_WIDTH-1:0]       data_in,
    input  wire                        valid_in,
    output wire                        ready_out,
    output wire [DATA_WIDTH-1:0]       data_out,
    output wire                        valid_out,
    input  wire                        ready_in
);

    reg [DATA_WIDTH-1:0] acc_reg;
    reg                   out_valid_reg;

    // ready_out: ready to accept new input when ready_in is high (no backpressure from output)
    assign ready_out = ready_in;

    // valid_out: high only after first accumulation
    assign valid_out = out_valid_reg;

    assign data_out = acc_reg;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            acc_reg <= {DATA_WIDTH{1'b0}};
            out_valid_reg <= 1'b0;
        end else begin
            if (valid_in && ready_out) begin
                acc_reg <= acc_reg + data_in;
                out_valid_reg <= 1'b1;
            end
        end
    end

endmodule
