module skid_buffer #(parameter DATA_WIDTH = 8) (
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] in_data,
    input in_valid,
    output in_ready,
    output [DATA_WIDTH-1:0] out_data,
    output out_valid,
    input out_ready
);

reg [DATA_WIDTH-1:0] reg0, reg1;
reg [1:0] count;

wire empty = (count == 0);
wire full = (count == 2);

assign in_ready = !full;
assign out_valid = !empty;
assign out_data = reg0;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 0;
        reg0 <= 0;
        reg1 <= 0;
    end else begin
        case (count)
            0: begin
                if (in_valid) begin
                    reg0 <= in_data;
                    count <= 1;
                end
            end
            1: begin
                if (in_valid && out_ready) begin
                    reg0 <= in_data;
                end else if (in_valid) begin
                    reg1 <= reg0;
                    reg0 <= in_data;
                    count <= 2;
                end else if (out_ready) begin
                    count <= 0;
                end
            end
            2: begin
                if (out_ready) begin
                    reg0 <= reg1;
                    count <= 1;
                end
            end
        endcase
    end
end

endmodule
