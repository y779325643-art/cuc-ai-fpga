`timescale 1ns / 1ps

module stream_stage #(
    parameter DATA_WIDTH = 8
)(
    input  wire                clk,
    input  wire                reset_n,
    input  wire [DATA_WIDTH-1:0] in_data,
    input  wire                in_valid,
    input  wire                out_ready,
    output reg  [DATA_WIDTH-1:0] out_data,
    output reg                 out_valid,
    output wire                in_ready
);

    reg [DATA_WIDTH-1:0] pipe_data;
    reg pipe_valid;

    always @(posedge clk) begin
        if (!reset_n) begin
            pipe_data  <= {DATA_WIDTH{1'b0}};
            pipe_valid <= 1'b0;
            out_data   <= {DATA_WIDTH{1'b0}};
            out_valid  <= 1'b0;
        end else begin
            // Input stage: capture if valid and we are ready
            if (in_valid && in_ready) begin
                pipe_data  <= in_data;
                pipe_valid <= 1'b1;
            end else begin
                if (out_valid && out_ready) begin
                    pipe_valid <= 1'b0;
                end
            end
            // Output stage: if pipe has data, output it
            if (pipe_valid && (!out_valid || out_ready)) begin
                out_data  <= pipe_data;
                out_valid <= 1'b1;
                pipe_valid <= 1'b0;
            end else if (out_valid && out_ready) begin
                out_valid <= 1'b0;
            end
        end
    end

    assign in_ready = !pipe_valid || (out_valid && out_ready);  // Can accept if pipeline empty or output consumed

endmodule
