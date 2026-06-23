module top (
    input clk,
    input rst_n,
    input wr_en,
    input [11:0] wr_data,
    input [7:0] wr_addr,
    input rd_en,
    input [7:0] rd_addr,
    output reg [11:0] rd_data
);
    reg [11:0] mem [0:255];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_data <= 12'd0;
        end else begin
            if (wr_en) begin
                mem[wr_addr] <= wr_data;
            end
            if (rd_en) begin
                rd_data <= mem[rd_addr];
            end
        end
    end
endmodule
