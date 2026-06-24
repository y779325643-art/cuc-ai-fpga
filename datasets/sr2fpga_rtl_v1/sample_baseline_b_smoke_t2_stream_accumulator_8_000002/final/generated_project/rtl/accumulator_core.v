module accumulator_core (
    input wire clk,
    input wire reset_n,
    input wire sample_valid,
    input wire [7:0] sample,
    output wire sample_ready,
    output reg [15:0] sum
);
    assign sample_ready = 1'b1;
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            sum <= 16'h0;
        end else if (sample_valid && sample_ready) begin
            sum <= sum + {8'b0, sample};
        end
    end
endmodule
