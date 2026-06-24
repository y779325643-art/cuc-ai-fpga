module stream_stage #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [WIDTH-1:0] out_data,
    input wire out_ready
);

reg [WIDTH-1:0] stage_data;
reg stage_valid;

assign in_ready = !stage_valid || out_ready;
assign out_valid = stage_valid;
assign out_data = stage_data;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        stage_valid <= 1'b0;
        stage_data <= {WIDTH{1'b0}};
    end else begin
        if (in_valid && in_ready) begin
            stage_data <= in_data;
            stage_valid <= 1'b1;
        end else if (out_ready) begin
            stage_valid <= 1'b0;
        end
    end
end

endmodule
