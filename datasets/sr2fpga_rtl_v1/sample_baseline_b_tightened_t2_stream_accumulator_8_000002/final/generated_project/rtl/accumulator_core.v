module accumulator_core #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [WIDTH-1:0] sample,
    output wire sample_ready,
    output reg [WIDTH-1:0] sum
);
    assign sample_ready = 1'b1; // Always ready to accept
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sum <= 8'd0;
        else if (sample_valid)
            sum <= sum + sample;
    end
endmodule
