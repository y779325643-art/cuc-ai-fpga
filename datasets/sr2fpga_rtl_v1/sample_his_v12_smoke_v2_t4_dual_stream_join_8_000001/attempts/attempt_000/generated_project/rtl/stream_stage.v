module stream_stage #(
    parameter DATA_WIDTH = 16
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                in_valid,
    input  wire [DATA_WIDTH-1:0] in_data,
    output wire                in_ready,
    output wire                out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input  wire                out_ready
);

    reg valid_reg;
    reg [DATA_WIDTH-1:0] data_reg;

    assign in_ready = !valid_reg || (valid_reg && out_ready);
    assign out_valid = valid_reg;
    assign out_data = data_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_reg <= 1'b0;
        end else begin
            if (!valid_reg) begin
                if (in_valid) begin
                    valid_reg <= 1'b1;
                    data_reg <= in_data;
                end
            end else begin
                if (out_ready) begin
                    if (in_valid) begin
                        data_reg <= in_data;
                    end else begin
                        valid_reg <= 1'b0;
                    end
                end
            end
        end
    end

endmodule
