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
    assign in_ready = out_ready;
    assign out_valid = in_valid;
    wire signed [DATA_WIDTH-1:0] reward_s = $signed(reward);
    wire signed [DATA_WIDTH-1:0] next_value_s = $signed(next_value);
    wire signed [DATA_WIDTH-1:0] gamma_s = $signed(gamma);
    wire signed [2*DATA_WIDTH-1:0] prod = gamma_s * next_value_s;
    wire signed [2*DATA_WIDTH-1:0] shifted = prod >>> SCALE_SHIFT;
    wire signed [DATA_WIDTH-1:0] scaled = shifted[DATA_WIDTH-1:0];
    wire signed [DATA_WIDTH:0] sum = reward_s + scaled;
    assign discounted_return = sum[DATA_WIDTH-1:0];
    wire _unused_shift_high = |shifted[2*DATA_WIDTH-1:DATA_WIDTH];
    wire _unused_sum_carry = sum[DATA_WIDTH];
endmodule
