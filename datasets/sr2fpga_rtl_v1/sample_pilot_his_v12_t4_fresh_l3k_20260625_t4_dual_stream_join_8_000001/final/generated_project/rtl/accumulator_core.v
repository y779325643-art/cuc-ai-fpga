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
    reg                   valid_reg;

    wire load   = valid_in && ready_out;
    wire unload = ready_in && valid_reg;

    assign ready_out = ~valid_reg || ready_in;
    assign valid_out = valid_reg;
    assign data_out  = acc_reg;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            acc_reg   <= {DATA_WIDTH{1'b0}};
            valid_reg <= 1'b0;
        end else begin
            if (load && unload) begin
                // simultaneous: replace data and remain valid
                acc_reg   <= acc_reg + data_in;
                // valid_reg stays 1
            end else if (load) begin
                acc_reg   <= acc_reg + data_in;
                valid_reg <= 1'b1;
            end else if (unload) begin
                valid_reg <= 1'b0;
            end
        end
    end

endmodule
