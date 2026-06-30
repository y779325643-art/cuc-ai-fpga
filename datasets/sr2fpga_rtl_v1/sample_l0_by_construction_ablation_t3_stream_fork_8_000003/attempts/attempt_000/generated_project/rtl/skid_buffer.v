module skid_buffer #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [WIDTH-1:0] out_data,
    input wire out_ready
);
    reg skid_valid;
    reg [WIDTH-1:0] skid_data;

    assign in_ready = !skid_valid || out_ready;
    assign out_valid = in_valid || skid_valid;
    assign out_data = skid_valid ? skid_data : in_data;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            skid_valid <= 1'b0;
            skid_data <= 0;
        end else begin
            if (in_ready && in_valid) begin
                if (out_ready) begin
                    skid_valid <= 1'b0;
                end else begin
                    skid_valid <= 1'b1;
                    skid_data <= in_data;
                end
            end else if (skid_valid && out_ready) begin
                skid_valid <= 1'b0;
            end
        end
    end
endmodule
