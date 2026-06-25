module stream_stage #(
    parameter WIDTH = 8
) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] in_data,
    input  wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] out_data,
    output wire out_valid,
    input  wire out_ready
);

    reg [WIDTH-1:0] out_data_reg;
    reg valid;

    assign in_ready = !valid || out_ready;
    assign out_data = out_data_reg;
    assign out_valid = valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid <= 1'b0;
            out_data_reg <= 0;
        end else if (in_valid & in_ready) begin
            out_data_reg <= in_data;
            valid <= 1'b1;
        end else if (out_ready & valid) begin
            valid <= 1'b0;
        end
    end

endmodule
