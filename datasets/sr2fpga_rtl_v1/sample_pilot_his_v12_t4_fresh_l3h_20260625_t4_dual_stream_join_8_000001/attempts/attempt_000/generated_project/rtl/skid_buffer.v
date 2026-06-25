`timescale 1ns / 1ps

module skid_buffer #(
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

    // Depth 2 skid buffer
    reg [DATA_WIDTH-1:0] buf0, buf1;
    reg empty, full;
    reg rd_ptr; // 0 = buf0, 1 = buf1

    always @(posedge clk) begin
        if (!reset_n) begin
            out_valid <= 1'b0;
            out_data  <= {DATA_WIDTH{1'b0}};
            buf0      <= {DATA_WIDTH{1'b0}};
            buf1      <= {DATA_WIDTH{1'b0}};
            empty     <= 1'b1;
            full      <= 1'b0;
            rd_ptr    <= 1'b0;
        end else begin
            // Write operation
            if (in_valid && in_ready) begin
                if (empty) begin
                    // Buffer empty: write directly to output register
                    out_data  <= in_data;
                    out_valid <= 1'b1;
                    empty     <= 1'b0;
                    full      <= 1'b0;
                end else if (!full) begin
                    // Buffer non-empty but not full: write to next slot
                    if (rd_ptr == 0) begin
                        buf1 <= in_data;
                        full <= 1'b1;
                    end else begin
                        buf0 <= in_data;
                        full <= 1'b1;
                    end
                end else begin
                    // Full: drop (should not happen if in_ready is deasserted when full)
                end
            end

            // Read operation (output consumed)
            if (out_valid && out_ready) begin
                if (full) begin
                    // There is a buffered sample
                    if (rd_ptr == 0) begin
                        out_data <= buf0;
                    end else begin
                        out_data <= buf1;
                    end
                    out_valid <= 1'b1;
                    full      <= 1'b0;
                    rd_ptr    <= ~rd_ptr;
                end else begin
                    out_valid <= 1'b0;
                    empty     <= 1'b1;
                end
            end
        end
    end

    assign in_ready = !full;

endmodule
