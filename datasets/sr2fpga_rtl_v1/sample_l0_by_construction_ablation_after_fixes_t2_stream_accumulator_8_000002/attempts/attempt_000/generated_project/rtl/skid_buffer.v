module skid_buffer #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    in_valid,
    input  wire [DATA_WIDTH-1:0]   in_data,
    output wire                    in_ready,
    output wire                    out_valid,
    output wire [DATA_WIDTH-1:0]   out_data,
    input  wire                    out_ready
);
    reg [DATA_WIDTH-1:0] data_reg;
    reg                  valid_reg;

    assign in_ready = !valid_reg || out_ready;
    assign out_data  = valid_reg ? data_reg : in_data;
    assign out_valid = valid_reg || in_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_reg <= 1'b0;
            data_reg  <= {DATA_WIDTH{1'b0}};
        end else begin
            if (out_ready && valid_reg) begin
                if (in_valid) begin
                    data_reg <= in_data;
                end else begin
                    valid_reg <= 1'b0;
                end
            end else if (in_valid && !out_ready && !valid_reg) begin
                data_reg <= in_data;
                valid_reg <= 1'b1;
            end
        end
    end
endmodule
