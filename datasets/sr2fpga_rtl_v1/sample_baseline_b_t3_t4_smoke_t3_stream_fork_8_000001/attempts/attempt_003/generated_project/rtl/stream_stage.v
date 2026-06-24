module stream_stage #(parameter WIDTH = 8) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] in_data,
    input in_valid,
    output reg in_ready,
    output reg [WIDTH-1:0] out_data,
    output reg out_valid,
    input out_ready
);

reg [WIDTH-1:0] pipe_data;
reg pipe_valid;

wire stall = out_valid && !out_ready;
wire load = in_valid && !stall;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        in_ready <= 1'b1;
        out_valid <= 1'b0;
        pipe_valid <= 1'b0;
    end else begin
        if (stall) begin
            // hold current output
            in_ready <= 1'b0;
        end else begin
            in_ready <= 1'b1;
            if (load) begin
                out_data <= in_data;
                out_valid <= in_valid;
            end else begin
                out_valid <= 1'b0;
            end
        end
    end
end

endmodule
