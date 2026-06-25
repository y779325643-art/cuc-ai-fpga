// stream_stage.v - Simple pipeline stage with valid-ready handshake
`timescale 1ns/1ps

module stream_stage #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    reset_n,
    input  wire [DATA_WIDTH-1:0]   in_data,
    input  wire                    in_valid,
    output wire                    in_ready,
    output reg [DATA_WIDTH-1:0]    out_data,
    output reg                     out_valid,
    input  wire                    out_ready
);

    reg stage_valid;
    reg [DATA_WIDTH-1:0] stage_data;

    assign in_ready = ~stage_valid; // Accept when stage is empty

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            stage_valid <= 1'b0;
            stage_data <= 0;
            out_data <= 0;
            out_valid <= 1'b0;
        end else begin
            // Transfer from stage to output if output ready
            if (out_valid && out_ready) begin
                out_valid <= 1'b0;
            end
            // If stage has data and output is free, move to output
            if (stage_valid && !out_valid) begin
                out_data <= stage_data;
                out_valid <= 1'b1;
                stage_valid <= 1'b0;
            end
            // Accept new data if stage empty
            if (in_valid && in_ready) begin
                stage_data <= in_data;
                stage_valid <= 1'b1;
            end
        end
    end

endmodule
