module stream_join #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [WIDTH-1:0] in0_data,
    output wire in0_ready,
    input wire in1_valid,
    input wire [WIDTH-1:0] in1_data,
    output wire in1_ready,
    output wire out_valid,
    output wire [WIDTH-1:0] out_data,
    input wire out_ready
);

reg [WIDTH-1:0] join_data;
reg join_valid;
wire both_valid;

assign both_valid = in0_valid && in1_valid;
assign in0_ready = (!join_valid || out_ready) && both_valid;
assign in1_ready = (!join_valid || out_ready) && both_valid;
assign out_valid = join_valid;
assign out_data = join_data;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        join_valid <= 1'b0;
        join_data <= {WIDTH{1'b0}};
    end else begin
        if (both_valid && (!join_valid || out_ready)) begin
            join_data <= in0_data + in1_data; // Join: addition
            join_valid <= 1'b1;
        end else if (out_ready) begin
            join_valid <= 1'b0;
        end
    end
end

endmodule
