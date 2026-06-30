// skid_buffer.v: standard skid buffer for back-pressured pipelines
module skid_buffer (
    input clk,
    input rst_n,
    input       in_valid,
    input [7:0] in_data,
    output      in_ready,
    output reg  out_valid,
    output reg [7:0] out_data,
    input       out_ready
);

reg        full;   // 1 indicates output register holds valid data
reg [7:0]  storage;

// in_ready is high when the buffer can accept a new word
assign in_ready = !full || out_ready;

// out_valid is high when the output register holds valid data
// already registered as out_valid

// out_data is driven by out_data register

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        full <= 1'b0;
        out_data <= 8'd0;
        out_valid <= 1'b0;
    end else begin
        if (full) begin
            // we have stored data
            if (out_ready) begin
                // output data is being taken
                if (in_valid && in_ready) begin
                    // accept new data and replace
                    out_data <= in_data;
                    full <= 1'b1;
                end else begin
                    // no new data, go empty
                    full <= 1'b0;
                    out_data <= out_data; // keep previous data until overwritten
                end
                // out_valid goes low only if we become empty and no new data is arriving
                out_valid <= in_valid && in_ready;
            end else begin
                // output not ready, keep full and data stable
                // can we accept new data? in_ready = !full || out_ready = 0, so no
                // do nothing
                out_valid <= 1'b1;
            end
        end else begin
            // buffer empty
            if (in_valid) begin
                // accept incoming data
                out_data <= in_data;
                full <= 1'b1;
                out_valid <= 1'b1;
            end else begin
                out_valid <= 1'b0;
                full <= 1'b0;
            end
        end
    end
end

endmodule
