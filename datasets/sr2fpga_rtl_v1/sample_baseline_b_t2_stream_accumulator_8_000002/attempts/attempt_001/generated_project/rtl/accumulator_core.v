module accumulator_core #(
    parameter WIDTH = 8
)(
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [WIDTH-1:0] sample,
    output reg [WIDTH-1:0] sum,
    output wire sample_ready
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum <= 0;
        end else begin
            if (sample_valid) begin
                sum <= sum + sample;
            end
        end
    end

    assign sample_ready = 1'b1;
endmodule
