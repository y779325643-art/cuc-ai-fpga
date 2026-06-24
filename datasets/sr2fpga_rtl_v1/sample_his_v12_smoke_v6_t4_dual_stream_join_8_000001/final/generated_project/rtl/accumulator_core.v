`timescale 1ns / 1ps

module accumulator_core #(parameter WIDTH = 8) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH*2-1:0] data_in,
    input  wire valid_in,
    output wire ready_out,
    output wire [WIDTH-1:0] data_out,
    output wire valid_out,
    input  wire ready_in
);

    reg [WIDTH-1:0] acc_reg;
    reg valid_reg;

    // ready_out: always ready to accept if we are not holding a valid output that hasn't been taken
    assign ready_out = !valid_reg || ready_in;
    assign data_out = acc_reg;
    assign valid_out = valid_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_reg <= {WIDTH{1'b0}};
            valid_reg <= 1'b0;
        end else begin
            if (valid_reg) begin
                // We have a valid output: if ready_in is high, we clear valid_reg
                if (ready_in) begin
                    valid_reg <= 1'b0;
                end
            end
            if (valid_in && ready_out) begin
                // Input accepted: accumulate
                // Add the two halves: data_in[WIDTH-1:0] and data_in[2*WIDTH-1:WIDTH]
                acc_reg <= acc_reg + data_in[WIDTH-1:0] + data_in[2*WIDTH-1:WIDTH];
                valid_reg <= 1'b1;
            end
        end
    end

endmodule
