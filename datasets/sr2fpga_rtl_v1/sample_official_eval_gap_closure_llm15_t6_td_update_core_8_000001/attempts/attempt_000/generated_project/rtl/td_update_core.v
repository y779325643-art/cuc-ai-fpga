module td_update_core #(parameter DATA_WIDTH = 8, parameter SCALE_SHIFT = 4) (
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] discounted_return,
    input wire [DATA_WIDTH-1:0] value,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] td_error,
    output wire [DATA_WIDTH-1:0] updated_value
);
    // Combinational TD update logic
    wire signed [8:0] diff;
    wire signed [15:0] mul_a;
    wire signed [7:0] shifted_mul_a;
    wire signed [8:0] sum_val;
    wire _unused_diff_high;
    wire _unused_sum_val_high;

    assign diff = $signed(discounted_return) - $signed(value);
    assign td_error = diff[DATA_WIDTH-1:0];
    assign _unused_diff_high = diff[DATA_WIDTH];

    assign mul_a = $signed(alpha) * $signed(td_error);
    assign shifted_mul_a = mul_a >>> SCALE_SHIFT;
    assign sum_val = $signed(value) + $signed(shifted_mul_a);
    assign updated_value = sum_val[DATA_WIDTH-1:0];
    assign _unused_sum_val_high = sum_val[DATA_WIDTH];

    assign out_valid = in_valid;
    assign in_ready = out_ready;
endmodule
