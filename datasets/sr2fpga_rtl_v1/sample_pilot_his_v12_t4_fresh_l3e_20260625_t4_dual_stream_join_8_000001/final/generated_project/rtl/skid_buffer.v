module skid_buffer #(
    parameter DATA_WIDTH = 8
) (
    input  wire                 clk,
    input  wire                 reset_n,
    input  wire                 in_valid,
    output reg                  in_ready,
    input  wire [DATA_WIDTH-1:0] in_data,
    output reg                  out_valid,
    input  wire                 out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

    reg [DATA_WIDTH-1:0] buffer_data;
    reg                  buffer_valid;
    reg                  buffer_full;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            in_ready <= 1'b0;
            out_valid <= 1'b0;
            out_data <= {DATA_WIDTH{1'b0}};
            buffer_valid <= 1'b0;
            buffer_full <= 1'b0;
            buffer_data <= {DATA_WIDTH{1'b0}};
        end else begin
            // Default assignments
            in_ready <= 1'b0;
            out_valid <= 1'b0;
            if (buffer_full) begin
                // Buffer holds data, must output it
                out_valid <= 1'b1;
                out_data <= buffer_data;
                if (out_ready) begin
                    buffer_full <= 1'b0;
                    buffer_valid <= 1'b0;
                end
            end else if (buffer_valid) begin
                // Data in buffer but not full (should not happen)
                out_valid <= 1'b1;
                out_data <= buffer_data;
                if (out_ready) begin
                    buffer_valid <= 1'b0;
                end
            end
            // Input handling
            if (!buffer_full && in_valid) begin
                // Can accept input
                in_ready <= 1'b1;
                if (buffer_valid) begin
                    // Buffer already has data, move to full
                    buffer_full <= 1'b1;
                    buffer_data <= in_data;
                end else begin
                    // No data in buffer, store or bypass
                    if (out_ready) begin
                        // Bypass directly to output
                        out_valid <= 1'b1;
                        out_data <= in_data;
                    end else begin
                        // Store in buffer
                        buffer_valid <= 1'b1;
                        buffer_data <= in_data;
                    end
                end
            end
        end
    end

endmodule
