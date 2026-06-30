module accumulator_core #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    sample_valid,
    input  wire [DATA_WIDTH-1:0]   sample,
    output reg                     sample_ready,
    output reg  [DATA_WIDTH-1:0]   sum
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum <= {DATA_WIDTH{1'b0}};
        end else if (sample_valid) begin
            sum <= sum + sample;
        end
    end

    always @(*) begin
        sample_ready = 1'b1;
    end
endmodule
