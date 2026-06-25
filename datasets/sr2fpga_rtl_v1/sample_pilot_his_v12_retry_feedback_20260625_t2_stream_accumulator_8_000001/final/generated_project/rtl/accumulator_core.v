`timescale 1ns / 1ps
module accumulator_core (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_valid,
    output wire        in_ready,
    input  wire [7:0]  in_data,
    output wire        out_valid,
    input  wire        out_ready,
    output wire [7:0]  out_data
);
    parameter DATA_WIDTH = 8;
    reg [DATA_WIDTH-1:0] accum_reg;
    reg started;
    wire accept_input = in_valid & in_ready;
    wire transfer_out = out_valid & out_ready;
    assign in_ready = ~started | out_ready;
    assign out_valid = started;
    assign out_data = accum_reg;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            accum_reg <= {DATA_WIDTH{1'b0}};
            started <= 1'b0;
        end else begin
            if (accept_input) begin
                accum_reg <= accum_reg + in_data;
                started <= 1'b1;
            end
        end
    end
endmodule
