// accumulator_core.v - Accumulates input data and outputs result
`timescale 1ns/1ps

module accumulator_core #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    reset_n,
    input  wire [DATA_WIDTH-1:0]   in_data,
    input  wire                    in_valid,
    output reg                     in_ready,
    output reg [DATA_WIDTH-1:0]    out_data,
    output reg                     out_valid,
    input  wire                    out_ready
);

    reg [DATA_WIDTH-1:0] accumulator_reg;

    // In ready: always ready unless output is valid and not being read? Actually we need to prevent overflow.
    // Simple: ready when not outputting valid? Or when output ready? We'll make in_ready = !out_valid || out_ready;
    // Actually to avoid deadlock, in_ready should be high when we can accept new data.
    assign in_ready = ~out_valid | out_ready;

    // Accumulation logic
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            accumulator_reg <= 0;
            out_data <= 0;
            out_valid <= 1'b0;
        end else begin
            // If we are outputting and out_ready, clear valid
            if (out_valid && out_ready) begin
                out_valid <= 1'b0;
            end
            // If input valid and we are ready (in_ready), accumulate
            if (in_valid && in_ready) begin
                accumulator_reg <= accumulator_reg + in_data;
                out_data <= accumulator_reg + in_data; // Update output to new accumulated value
                out_valid <= 1'b1;
            end
        end
    end

endmodule
