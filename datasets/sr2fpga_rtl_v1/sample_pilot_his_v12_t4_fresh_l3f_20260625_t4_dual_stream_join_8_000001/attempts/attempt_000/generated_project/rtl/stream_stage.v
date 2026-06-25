module stream_stage #(parameter DATA_WIDTH=8) (
    input clk, rst_n,
    input in_valid,
    output in_ready,
    input [DATA_WIDTH-1:0] in_data,
    output reg out_valid,
    input out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

reg pipe_valid;
reg [DATA_WIDTH-1:0] pipe_data;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pipe_valid <= 0;
        out_valid <= 0;
    end else begin
        if (out_ready && out_valid) begin
            pipe_valid <= 0;
        end
        if (in_valid && out_ready) begin
            pipe_valid <= 1;
            pipe_data <= in_data;
        end
        out_valid <= pipe_valid;
        out_data <= pipe_data;
    end
end

assign in_ready = out_ready;

endmodule
