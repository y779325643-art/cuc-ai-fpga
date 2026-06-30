// stream_stage.v: a single pipeline stage with valid/ready handshake
module stream_stage (
    input clk,
    input rst_n,
    input       in_valid,
    input [7:0] in_data,
    output      in_ready,
    output reg  out_valid,
    output reg [7:0] out_data,
    input       out_ready
);

reg       full;   // 1 if output register holds valid data
reg [7:0] storage;

// in_ready: we can accept new data if we are empty, or if we are full but downstream is ready (so we can replace stored data in the same cycle)
assign in_ready = !full || out_ready;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        full      <= 1'b0;
        storage   <= 8'd0;
        out_valid <= 1'b0;
        out_data  <= 8'd0;
    end else begin
        if (full) begin
            // we have data to output
            if (out_ready) begin
                // downstream is reading our data
                if (in_valid && in_ready) begin
                    // accept new data and update output
                    storage  <= in_data;
                    full     <= 1'b1;  // stay full
                    out_data <= in_data;
                end else begin
                    // no new data, go empty
                    full     <= 1'b0;
                end
                // out_valid: stays high only if new data arrived; else low
                out_valid <= in_valid && in_ready;
            end else begin
                // out_ready low, hold data
                // cannot accept new input because in_ready = !full || out_ready = 0
                out_valid <= 1'b1;
            end
        end else begin
            // empty
            if (in_valid) begin
                // accept new data
                storage   <= in_data;
                full      <= 1'b1;
                out_data  <= in_data;
                out_valid <= 1'b1;
            end else begin
                out_valid <= 1'b0;
                full      <= 1'b0;
            end
        end
    end
end

endmodule
