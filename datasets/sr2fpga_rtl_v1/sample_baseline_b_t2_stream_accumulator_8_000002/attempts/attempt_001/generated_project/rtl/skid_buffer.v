module skid_buffer #(
    parameter WIDTH = 8
)(
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    output reg out_valid,
    output reg [WIDTH-1:0] out_data,
    input wire out_ready,
    output reg in_ready
);
    reg valid;
    reg [WIDTH-1:0] data;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid <= 1'b0;
            data <= 0;
        end else begin
            if (in_valid && in_ready) begin
                data <= in_data;
                valid <= 1'b1;
            end else if (out_ready && out_valid) begin
                valid <= 1'b0;
            end
        end
    end

    assign out_valid = valid;
    assign out_data = data;
    assign in_ready = ~valid | out_ready;
endmodule
