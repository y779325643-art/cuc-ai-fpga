module skid_buffer #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    input wire out_ready,
    output wire out_valid,
    output wire [WIDTH-1:0] out_data
);
    reg skid_valid;
    reg [WIDTH-1:0] skid_data;
    reg bypass_valid;
    reg [WIDTH-1:0] bypass_data;
    wire use_skid;
    assign use_skid = out_ready ? 1'b0 : (bypass_valid || (in_valid && !out_ready));
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            skid_valid <= 1'b0;
            bypass_valid <= 1'b0;
        end else begin
            if (use_skid) begin
                if (!skid_valid) begin
                    skid_valid <= bypass_valid;
                    skid_data <= bypass_data;
                end else if (out_ready) begin
                    skid_valid <= 1'b0;
                end
            end
            if (in_valid && (!bypass_valid || out_ready)) begin
                bypass_valid <= 1'b1;
                bypass_data <= in_data;
            end else if (out_ready) begin
                bypass_valid <= 1'b0;
            end
        end
    end
    assign out_valid = bypass_valid | skid_valid;
    assign out_data = (skid_valid && !bypass_valid) ? skid_data : bypass_data;
endmodule
