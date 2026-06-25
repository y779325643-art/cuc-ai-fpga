// Single-entry skid buffer for backpressure tolerance
`timescale 1ns / 1ps

module skid_buffer #(
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

    reg [DATA_WIDTH-1:0] buf_data;
    reg                  buf_valid;

    wire pass_through = ~buf_valid;

    assign s_in_ready = ~buf_valid || s_out_ready;
    assign s_out_data = buf_valid ? buf_data : s_in_data;
    assign s_out_valid = buf_valid || (s_in_valid && pass_through);

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            buf_data  <= {DATA_WIDTH{1'b0}};
            buf_valid <= 1'b0;
        end else begin
            if (s_in_ready && s_in_valid) begin
                if (s_out_ready && buf_valid) begin
                    // simultaneous unload and load: output accepts previous buffer, load new
                    buf_data <= s_in_data;
                    // buf_valid stays 1
                end else if (~s_out_ready && ~buf_valid) begin
                    // store because output not ready
                    buf_data <= s_in_data;
                    buf_valid <= 1'b1;
                end
                // else: pass-through (output ready and buffer empty), no storage needed
            end else if (s_out_ready && buf_valid) begin
                // unload only
                buf_valid <= 1'b0;
            end
        end
    end

endmodule
