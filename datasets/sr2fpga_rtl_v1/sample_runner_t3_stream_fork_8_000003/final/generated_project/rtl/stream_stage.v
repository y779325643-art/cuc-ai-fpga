module stream_stage #(parameter WIDTH=8) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] in_data,
    input in_valid,
    output in_ready,
    output [WIDTH-1:0] out_data,
    output out_valid,
    input out_ready
);
    reg [WIDTH-1:0] data_reg;
    reg valid_reg;
    assign in_ready = !valid_reg || out_ready;
    assign out_valid = valid_reg;
    assign out_data = data_reg;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_reg <= 0;
            data_reg <= 0;
        end else begin
            if (out_ready && valid_reg) begin
                valid_reg <= 0;
            end
            if (in_valid && in_ready) begin
                data_reg <= in_data;
                valid_reg <= 1;
            end
        end
    end
endmodule
