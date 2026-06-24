module accumulator_core (
    input clk,
    input rst_n,
    input sample_valid,
    input [7:0] sample,
    output reg sample_ready,
    output reg [7:0] sum
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum <= 8'd0;
            sample_ready <= 1'b1;
        end else begin
            if (sample_valid & sample_ready) begin
                sum <= sum + sample;
            end
            sample_ready <= 1'b1; // always ready
        end
    end

endmodule
