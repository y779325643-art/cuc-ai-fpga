`timescale 1ns / 1ps

module skid_buffer #(parameter WIDTH = 8) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] data_in,
    input  wire valid_in,
    output wire ready_out,
    output wire [WIDTH-1:0] data_out,
    output wire valid_out,
    input  wire ready_in
);

    reg [WIDTH-1:0] buffer_reg;
    reg full;

    // ready_out: accept input if not full
    assign ready_out = !full;
    // valid_out: we have data if full
    assign valid_out = full;
    assign data_out = buffer_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            full <= 1'b0;
            buffer_reg <= {WIDTH{1'b0}};
        end else begin
            // Update full and buffer
            if (!full) begin
                // Buffer empty: can load if valid_in
                if (valid_in) begin
                    buffer_reg <= data_in;
                    full <= 1'b1;
                end
            end else begin
                // Buffer full: if downstream ready, we output and possibly load new data
                if (ready_in) begin
                    if (valid_in) begin
                        // Simultaneous output and input: update buffer
                        buffer_reg <= data_in;
                    end else begin
                        // No new input: buffer empties
                        full <= 1'b0;
                    end
                end
                // else stay full
            end
        end
    end

endmodule
