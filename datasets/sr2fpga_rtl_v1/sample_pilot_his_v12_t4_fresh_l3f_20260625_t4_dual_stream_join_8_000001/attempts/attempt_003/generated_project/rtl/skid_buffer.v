module skid_buffer #(parameter DATA_WIDTH=8) (
    input clk, rst_n,
    input in_valid,
    output reg in_ready,
    input [DATA_WIDTH-1:0] in_data,
    output reg out_valid,
    input out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

reg [DATA_WIDTH-1:0] buf0, buf1;
reg valid0, valid1;
wire push = in_valid && in_ready;
wire pop = out_ready && out_valid;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        valid0 <= 0;
        valid1 <= 0;
        out_valid <= 0;
    end else begin
        if (pop) begin
            valid0 <= valid1;
            buf0 <= buf1;
            valid1 <= 0;
        end
        if (push) begin
            if (!valid0) begin
                valid0 <= 1;
                buf0 <= in_data;
            end else if (!valid1) begin
                valid1 <= 1;
                buf1 <= in_data;
            end
        end
        out_valid <= valid0;
        out_data <= buf0;
    end
end

assign in_ready = !(valid0 && valid1);

endmodule
