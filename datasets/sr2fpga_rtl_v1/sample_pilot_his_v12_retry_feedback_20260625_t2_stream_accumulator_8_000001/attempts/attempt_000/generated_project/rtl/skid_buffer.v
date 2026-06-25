`timescale 1ns / 1ps
module skid_buffer (
    clk,
    rst_n,
    in_valid,
    in_ready,
    in_data,
    out_valid,
    out_ready,
    out_data
);
    parameter DATA_WIDTH = 8;

    input  wire                clk;
    input  wire                rst_n;
    input  wire                in_valid;
    output reg                 in_ready;
    input  wire [DATA_WIDTH-1:0] in_data;
    output reg                 out_valid;
    input  wire                out_ready;
    output reg  [DATA_WIDTH-1:0] out_data;

    reg [DATA_WIDTH-1:0] buf0_data;
    reg                  buf0_valid;
    reg [DATA_WIDTH-1:0] buf1_data;
    reg                  buf1_valid;
    reg [1:0]            count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buf0_valid <= 1'b0;
            buf1_valid <= 1'b0;
            count      <= 2'b0;
            out_valid  <= 1'b0;
            out_data   <= {DATA_WIDTH{1'b0}};
            in_ready   <= 1'b1;
        end else begin
            // Default assignments
            in_ready <= 1'b0;
            if (count < 2) begin
                in_ready <= 1'b1;
            end

            // Output logic
            if (out_valid && out_ready) begin
                // Output transferred: shift buffer
                if (buf0_valid) begin
                    out_valid <= 1'b0;
                end else begin
                    // buf0 invalid, but buf1 valid? Actually out_valid requires at least one valid.
                    // We'll handle in combinational output
                end
            end

            // Input acceptance
            if (in_valid && in_ready) begin
                if (!buf0_valid) begin
                    buf0_valid <= 1'b1;
                    buf0_data  <= in_data;
                end else if (!buf1_valid) begin
                    buf1_valid <= 1'b1;
                    buf1_data  <= in_data;
                end
            end

            // Update count based on valid flags
            count = (buf0_valid + buf1_valid);

            // Output mux
            if (buf0_valid) begin
                out_valid <= 1'b1;
                out_data  <= buf0_data;
            end else if (buf1_valid) begin
                out_valid <= 1'b1;
                out_data  <= buf1_data;
            end else begin
                out_valid <= 1'b0;
            end

            // If output transferred, shift
            if (out_valid && out_ready) begin
                if (buf0_valid) begin
                    buf0_valid <= 1'b0;
                    buf0_data  <= {DATA_WIDTH{1'b0}};
                end
                // Shift buf1 to buf0 if buf0 was taken
                if (buf1_valid && !buf0_valid) begin
                    buf0_valid <= 1'b1;
                    buf0_data  <= buf1_data;
                    buf1_valid <= 1'b0;
                end
            end
        end
    end

    // Update count combinational (also in always block, but for simulation clock edge, we can use wire)
    always @* begin
        count = buf0_valid + buf1_valid;
    end

endmodule
