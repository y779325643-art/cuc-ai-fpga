// stream_join.v: synchronizes two valid/ready streams and outputs their sum
module stream_join (
    input clk,
    input rst_n,
    input       in0_valid,
    input [7:0] in0_data,
    output      in0_ready,
    input       in1_valid,
    input [7:0] in1_data,
    output      in1_ready,
    output reg  out_valid,
    output reg [7:0] out_data,
    input       out_ready
);

// internal storage for each input when it arrives before the other
reg        has_i0, has_i1;
reg [7:0]  stored_i0, stored_i1;

// ready = can accept new data for this input when we don't already have stored data
assign in0_ready = !has_i0;
assign in1_ready = !has_i1;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        has_i0   <= 1'b0;
        has_i1   <= 1'b0;
        stored_i0 <= 8'd0;
        stored_i1 <= 8'd0;
        out_valid <= 1'b0;
        out_data  <= 8'd0;
    end else begin
        // capture incoming data when valid and ready
        if (in0_valid && in0_ready) begin
            has_i0 <= 1'b1;
            stored_i0 <= in0_data;
        end else if (has_i0 && out_valid && out_ready) begin
            // consumed, clear has_i0 only if both present and handshake
            // but we only clear when a valid output handshake occurs, handled below
        end

        if (in1_valid && in1_ready) begin
            has_i1 <= 1'b1;
            stored_i1 <= in1_data;
        end

        // output handshake: if both inputs are present and output ready, output sum and clear stored flags
        if (out_valid && out_ready) begin
            // clear flags
            has_i0 <= 1'b0;
            has_i1 <= 1'b0;
            out_valid <= 1'b0;
        end

        // determine if we can produce output
        if (!out_valid || out_ready) begin
            // we can potentially produce a new output if both inputs are available
            if (has_i0 && has_i1) begin
                out_valid <= 1'b1;
                out_data  <= stored_i0 + stored_i1;
                // flags will be cleared on the next cycle's handshake
            end else begin
                // not yet both available, if we weren't already outputting, stay low
                // if we were outputting and out_ready but no new data, out_valid goes low (handled above)
            end
        end

        // special case: simultaneous arrival of new data and clearance
        if (in0_valid && in0_ready) begin
            // if this occurs while output handshake is happening, we need to update stored data
            // but the clone above to set has_i0 and stored_i0 will overwrite any earlier assignment,
            // which is what we want (latest assignment wins in same block). OK.
        end
    end
end

endmodule
