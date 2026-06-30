module stream_stage #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [WIDTH-1:0] out_data,
    input wire out_ready
);
    reg out_valid_reg;
    reg [WIDTH-1:0] out_data_reg;

    wire fire = in_valid && in_ready;
    assign in_ready = !out_valid_reg || out_ready;
    assign out_valid = out_valid_reg;
    assign out_data = out_data_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_valid_reg <= 1'b0;
            out_data_reg <= 0;
        end else begin
            if (fire) begin
                out_valid_reg <= 1'b1;
                out_data_reg <= in_data;
            end else if (out_ready && out_valid_reg) begin
                out_valid_reg <= 1'b0;
            end
        end
    end
endmodule
