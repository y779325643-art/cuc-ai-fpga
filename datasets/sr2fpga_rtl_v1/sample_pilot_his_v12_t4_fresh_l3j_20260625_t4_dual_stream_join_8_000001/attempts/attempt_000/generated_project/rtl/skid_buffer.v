module skid_buffer #(
    parameter DATA_WIDTH = 8
)(
    input  wire clk,
    input  wire rst_n,
    input  wire valid_in,
    output wire ready_in,
    input  wire [DATA_WIDTH-1:0] data_in,
    output wire valid_out,
    input  wire ready_out,
    output wire [DATA_WIDTH-1:0] data_out
);

    reg skid_valid;
    reg [DATA_WIDTH-1:0] skid_data;
    reg bypass;

    wire fifo_full = skid_valid;

    assign ready_in = !fifo_full || (bypass && ready_out);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            skid_valid <= 1'b0;
            bypass <= 1'b0;
        end else begin
            if (!fifo_full) begin
                // Empty, can accept
                if (valid_in) begin
                    if (ready_out) begin
                        // Pass through directly
                        bypass <= 1'b1;
                        skid_valid <= 1'b0;
                    end else begin
                        // Store
                        skid_data <= data_in;
                        skid_valid <= 1'b1;
                        bypass <= 1'b0;
                    end
                end else begin
                    bypass <= 1'b0;
                end
            end else begin
                // Full
                if (ready_out) begin
                    // Output stored data
                    if (valid_in) begin
                        // Replace with new data
                        skid_data <= data_in;
                        skid_valid <= 1'b1;
                        bypass <= 1'b0;
                    end else begin
                        skid_valid <= 1'b0;
                        bypass <= 1'b0;
                    end
                end else begin
                    // Hold
                end
            end
        end
    end

    assign valid_out = bypass ? valid_in : skid_valid;
    assign data_out = bypass ? data_in : skid_data;

endmodule
