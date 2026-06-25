// Simple pipeline register stage (single flop) for output
`timescale 1ns / 1ps

module stream_stage #(
    parameter DATA_WIDTH = 8
) (
    input  wire                        clk,
    input  wire                        reset_n,
    input  wire [DATA_WIDTH-1:0]       s_in_data,
    input  wire                        s_in_valid,
    output wire                        s_in_ready,
    output wire [DATA_WIDTH-1:0]       s_out_data,
    output wire                        s_out_valid,
    input  wire                        s_out_ready
);

    reg                  pipe_valid;
    reg [DATA_WIDTH-1:0] pipe_data;

    assign s_in_ready = ~pipe_valid || s_out_ready;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            pipe_valid <= 1'b0;
        end else begin
            if (s_in_ready && s_in_valid) begin
                pipe_data  <= s_in_data;
                pipe_valid <= 1'b1;
            end else if (s_out_ready) begin
                pipe_valid <= 1'b0;
            end
        end
    end

    assign s_out_data  = pipe_data;
    assign s_out_valid = pipe_valid;

endmodule
