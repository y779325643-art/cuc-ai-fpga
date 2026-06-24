module accumulator_core #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [WIDTH-1:0] sample,
    output wire sample_ready,
    output wire out_valid,
    output wire [WIDTH-1:0] out_data,
    input wire out_ready
);

reg [WIDTH-1:0] sum;
reg valid;

assign sample_ready = !valid || out_ready;
assign out_valid = valid;
assign out_data = sum;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        sum <= {WIDTH{1'b0}};
        valid <= 1'b0;
    end else begin
        if (sample_valid && sample_ready) begin
            sum <= sum + sample;
            valid <= 1'b1;
        end else if (out_ready) begin
            valid <= 1'b0;
        end
    end
end

endmodule
