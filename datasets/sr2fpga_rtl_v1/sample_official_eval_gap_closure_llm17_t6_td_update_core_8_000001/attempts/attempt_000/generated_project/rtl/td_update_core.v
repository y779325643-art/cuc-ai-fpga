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
    assign in_ready = out_ready;
    assign out_valid = in_valid;
    wire signed [DATA_WIDTH-1:0] discounted_return_s = $signed(discounted_return);
    wire signed [DATA_WIDTH-1:0] value_s = $signed(value);
    wire signed [DATA_WIDTH-1:0] alpha_s = $signed(alpha);
    wire signed [DATA_WIDTH-1:0] td_error_s = discounted_return_s - value_s;
    wire signed [2*DATA_WIDTH-1:0] prod = alpha_s * td_error_s;
    wire signed [2*DATA_WIDTH-1:0] shifted = prod >>> SCALE_SHIFT;
    wire signed [DATA_WIDTH-1:0] scaled = shifted[DATA_WIDTH-1:0];
    wire signed [DATA_WIDTH:0] new_val = value_s + scaled;
    assign td_error = td_error_s;
    assign updated_value = new_val[DATA_WIDTH-1:0];
    wire _unused_shift_high = |shifted[2*DATA_WIDTH-1:DATA_WIDTH];
    wire _unused_carry = new_val[DATA_WIDTH];
endmodule
