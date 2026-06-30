module discount_core #(parameter DATA_WIDTH = 8, parameter SCALE_SHIFT = 4) (
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] next_value,
    input wire [DATA_WIDTH-1:0] gamma,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] discounted_return
);
    // Combinational discount logic
    wire signed [15:0] mul;
    wire signed [7:0] shifted_mul;
    wire signed [8:0] sum;
    wire _unused_sum_high;

    assign mul = $signed(gamma) * $signed(next_value);
    assign shifted_mul = mul >>> SCALE_SHIFT;
    assign sum = $signed(reward) + $signed(shifted_mul);
    assign discounted_return = sum[DATA_WIDTH-1:0];
    assign _unused_sum_high = sum[DATA_WIDTH];

    assign out_valid = in_valid;
    assign in_ready = out_ready;
endmodule
