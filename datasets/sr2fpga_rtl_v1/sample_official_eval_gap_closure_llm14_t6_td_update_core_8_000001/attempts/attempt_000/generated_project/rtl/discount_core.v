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
    // Combinational ready/valid passthrough
    assign in_ready  = out_ready;
    assign out_valid = in_valid & out_ready;

    // Treat all operands as signed fixed-point.
    // gamma is Q4.4, reward and next_value are Q8.0.
    // Compute discounted_return = reward + (gamma * next_value) >>> SCALE_SHIFT
    wire signed [DATA_WIDTH-1:0] r   = $signed(reward);
    wire signed [DATA_WIDTH-1:0] nv  = $signed(next_value);
    wire signed [DATA_WIDTH-1:0] g   = $signed(gamma);

    // Multiply with enough width to avoid overflow
    wire signed [2*DATA_WIDTH-1:0] product = g * nv;
    wire signed [2*DATA_WIDTH-1:0] shifted = product >>> SCALE_SHIFT;
    wire signed [2*DATA_WIDTH-1:0] sum     = r + shifted;

    // Truncate/saturate to DATA_WIDTH bits (no explicit saturation)
    assign discounted_return = sum[DATA_WIDTH-1:0];
endmodule
