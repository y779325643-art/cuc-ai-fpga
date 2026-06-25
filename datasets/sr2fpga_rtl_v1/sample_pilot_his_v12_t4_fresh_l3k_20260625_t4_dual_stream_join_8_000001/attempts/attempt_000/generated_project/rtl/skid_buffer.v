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

    reg                  has_data;
    reg [DATA_WIDTH-1:0] buf_data;
    reg                  buf_valid;

    wire                 pass_through = s_out_ready || ~buf_valid;
    wire                 skid_load   = s_in_valid && s_in_ready;

    assign s_in_ready = pass_through;
    assign s_out_data = buf_valid ? buf_data : s_in_data;
    assign s_out_valid = buf_valid || (s_in_valid && pass_through);

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            has_data  <= 1'b0;
            buf_valid <= 1'b0;
        end else begin
            if (s_out_ready) begin
                // output consumed
                if (has_data) begin
                    has_data <= 1'b0;
                    buf_valid <= 1'b0;
                end else begin
                    // nothing in buffer
                end
            end
            if (skid_load && ~pass_through) begin
                // load into skid buffer
                buf_data  <= s_in_data;
                has_data  <= 1'b1;
                buf_valid <= 1'b1;
            end else if (skid_load && pass_through) begin
                // pass-through, no skid
            end
        end
    end

endmodule
