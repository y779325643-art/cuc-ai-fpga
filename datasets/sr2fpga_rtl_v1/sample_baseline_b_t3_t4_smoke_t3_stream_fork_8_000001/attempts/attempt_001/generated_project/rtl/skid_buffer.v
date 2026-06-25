module skid_buffer #(parameter WIDTH = 8) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] in_data,
    input in_valid,
    output reg in_ready,
    output reg [WIDTH-1:0] out_data,
    output reg out_valid,
    input out_ready
);

reg [WIDTH-1:0] buf_data;
reg buf_valid;
reg skid_active;

wire pass_through = !skid_active && (!out_valid || out_ready);
wire skid_load = skid_active && out_ready;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        in_ready <= 1'b0;
        out_valid <= 1'b0;
        buf_valid <= 1'b0;
        skid_active <= 1'b0;
    end else begin
        // in_ready logic
        if (pass_through || (skid_active && out_ready))
            in_ready <= 1'b1;
        else
            in_ready <= 1'b0;
        // skid_active update
        if (in_valid && in_ready && !out_ready && out_valid)
            skid_active <= 1'b1;
        else if (skid_active && out_ready)
            skid_active <= 1'b0;
        // buf loading
        if (skid_active && out_ready)
            buf_valid <= 1'b0;
        else if (in_valid && in_ready && !out_ready && out_valid) begin
            buf_data <= in_data;
            buf_valid <= 1'b1;
        end
        // out_valid and out_data
        if (pass_through) begin
            out_valid <= in_valid;
            out_data <= in_data;
        end else if (skid_active && out_ready) begin
            out_valid <= buf_valid;
            out_data <= buf_data;
        end else if (skid_active && !out_ready) begin
            out_valid <= 1'b1;
            out_data <= buf_data;
        end else begin
            out_valid <= out_valid; // hold
            out_data <= out_data;
        end
    end
end

endmodule
