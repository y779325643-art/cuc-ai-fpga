module accumulator_core #(
    parameter WIDTH = 8
) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] in_data,
    input  wire in_valid,
    output wire in_ready,
    input  wire clear,
    output wire [WIDTH-1:0] out_data,
    output wire out_valid,
    input  wire out_ready
);

    reg [WIDTH-1:0] acc_reg;

    assign out_data = acc_reg;
    assign out_valid = 1'b1;
    assign in_ready = out_ready;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_reg <= 0;
        end else if (clear) begin
            acc_reg <= 0;
        end else if (in_valid & in_ready) begin
            acc_reg <= acc_reg + in_data;
        end
    end

endmodule
