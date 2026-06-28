module stream_fork #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out0_valid,
    output wire [WIDTH-1:0] out0_data,
    input wire out0_ready,
    output wire out1_valid,
    output wire [WIDTH-1:0] out1_data,
    input wire out1_ready
);
    reg busy;
    reg [WIDTH-1:0] data_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy <= 1'b0;
            data_reg <= 0;
        end else begin
            if (busy) begin
                if (out0_ready && out1_ready) begin
                    busy <= 1'b0;
                end
            end else begin
                if (in_valid) begin
                    busy <= 1'b1;
                    data_reg <= in_data;
                end
            end
        end
    end

    assign in_ready = !busy;
    assign out0_valid = busy;
    assign out0_data = data_reg;
    assign out1_valid = busy;
    assign out1_data = data_reg;
endmodule
