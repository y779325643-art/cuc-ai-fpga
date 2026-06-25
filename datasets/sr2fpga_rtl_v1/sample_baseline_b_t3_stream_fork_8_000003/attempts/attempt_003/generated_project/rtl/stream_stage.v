module stream_stage #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [WIDTH-1:0] out_data
);

    reg [WIDTH-1:0] data_reg;
    reg valid_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_reg <= 1'b0;
        end else begin
            if (in_valid && in_ready) begin
                data_reg <= in_data;
                valid_reg <= 1'b1;
            end else if (out_ready && out_valid) begin
                valid_reg <= 1'b0;
            end
        end
    end

    assign in_ready = !valid_reg || (out_ready && out_valid);
    assign out_valid = valid_reg || (in_valid && in_ready);
    assign out_data = valid_reg ? data_reg : in_data;

endmodule
