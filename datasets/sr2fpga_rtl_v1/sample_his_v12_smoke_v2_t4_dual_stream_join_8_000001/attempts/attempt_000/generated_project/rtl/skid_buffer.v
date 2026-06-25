module skid_buffer #(
    parameter DATA_WIDTH = 8
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

    reg [DATA_WIDTH-1:0] buf0, buf1;
    reg [1:0] fill_count; // 0 empty, 1 one in buf0, 2 both
    reg [DATA_WIDTH-1:0] out_reg;
    reg out_valid_reg;

    wire pop = out_valid_reg && out_ready;
    wire push = in_valid && in_ready;

    assign in_ready = (fill_count < 2) ? 1'b1 : 1'b0;
    assign out_valid = out_valid_reg;
    assign out_data = out_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fill_count <= 2'b0;
            out_valid_reg <= 1'b0;
        end else begin
            case (fill_count)
                2'b00: begin
                    if (push) begin
                        // store in buf0
                        buf0 <= in_data;
                        fill_count <= 2'b01;
                        out_valid_reg <= 1'b1;
                        out_reg <= in_data;
                    end
                end
                2'b01: begin
                    if (pop) begin
                        if (push) begin
                            // push into buf0, no pop
                            buf0 <= in_data;
                            out_reg <= buf0;
                        end else begin
                            out_valid_reg <= 1'b0;
                            fill_count <= 2'b00;
                        end
                    end else begin
                        if (push) begin
                            buf1 <= in_data;
                            fill_count <= 2'b10;
                        end
                    end
                end
                2'b10: begin
                    if (pop) begin
                        out_reg <= buf1;
                        if (push) begin
                            buf0 <= in_data;
                            fill_count <= 2'b01;
                        end else begin
                            fill_count <= 2'b01;
                        end
                    end else begin
                        if (push) begin
                            // no space, should not happen due to in_ready
                        end
                    end
                end
            endcase
        end
    end

endmodule
