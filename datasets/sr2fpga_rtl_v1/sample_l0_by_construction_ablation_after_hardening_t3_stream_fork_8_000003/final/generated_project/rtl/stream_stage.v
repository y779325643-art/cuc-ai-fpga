`timescale 1ns / 1ps

module stream_stage #(
    parameter WIDTH = 8
) (
    input  wire        clk,
    input  wire        nreset,
    input  wire        in_valid,
    input  wire [WIDTH-1:0] in_data,
    output wire        in_ready,
    output wire        out_valid,
    output reg  [WIDTH-1:0] out_data,
    input  wire        out_ready
);

    reg out_valid_r;

    assign out_valid = out_valid_r;
    assign in_ready  = out_ready || !out_valid_r;

    always @(posedge clk or negedge nreset) begin
        if (!nreset) begin
            out_valid_r <= 1'b0;
            out_data     <= {WIDTH{1'b0}};
        end else begin
            if (out_ready || !out_valid_r) begin
                out_valid_r <= in_valid;
                out_data     <= in_data;
            end
        end
    end

endmodule
