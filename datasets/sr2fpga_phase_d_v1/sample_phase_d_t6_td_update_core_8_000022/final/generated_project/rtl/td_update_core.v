module td_update_core #(parameter DATA_WIDTH = 8) (
    input wire [DATA_WIDTH-1:0] reward_i,
    input wire [DATA_WIDTH-1:0] value_i,
    input wire [DATA_WIDTH-1:0] alpha_i,
    input wire [DATA_WIDTH-1:0] discounted_next_value_i,
    output wire [DATA_WIDTH-1:0] td_error_o,
    output wire [DATA_WIDTH-1:0] updated_value_o
);
  // SR2FPGA_BEHAVIOR_BEGIN
    localparam TD_EXT_WIDTH = DATA_WIDTH + 2;
    localparam UPDATE_PRODUCT_WIDTH = DATA_WIDTH * 2;

    wire signed [DATA_WIDTH-1:0] reward_signed;
    wire signed [DATA_WIDTH-1:0] value_signed;
    wire signed [DATA_WIDTH-1:0] discounted_signed;
    wire [DATA_WIDTH-1:0] alpha_unsigned;
    wire signed [TD_EXT_WIDTH-1:0] reward_ext;
    wire signed [TD_EXT_WIDTH-1:0] value_ext;
    wire signed [TD_EXT_WIDTH-1:0] discounted_ext;
    wire signed [TD_EXT_WIDTH-1:0] td_error_ext;
    wire signed [DATA_WIDTH-1:0] td_error_sliced;
    wire signed [UPDATE_PRODUCT_WIDTH:0] alpha_product_ext;
    wire signed [DATA_WIDTH:0] alpha_scaled_ext;
    wire signed [DATA_WIDTH:0] value_update_ext;
    wire [DATA_WIDTH-1:0] updated_value_slice;
    wire _unused_td_error_high_bits;
    wire _unused_alpha_product_low_bits;

    assign reward_signed = reward_i;
    assign value_signed = value_i;
    assign discounted_signed = discounted_next_value_i;
    assign alpha_unsigned = alpha_i;
    assign reward_ext = {{(TD_EXT_WIDTH-DATA_WIDTH){reward_signed[DATA_WIDTH-1]}}, reward_signed};
    assign value_ext = {{(TD_EXT_WIDTH-DATA_WIDTH){value_signed[DATA_WIDTH-1]}}, value_signed};
    assign discounted_ext = {{(TD_EXT_WIDTH-DATA_WIDTH){discounted_signed[DATA_WIDTH-1]}}, discounted_signed};
    assign td_error_ext = reward_ext + discounted_ext - value_ext;
    assign td_error_sliced = td_error_ext[DATA_WIDTH-1:0];
    assign alpha_product_ext = $signed(td_error_sliced) * $signed({1'b0, alpha_unsigned});
    assign alpha_scaled_ext = alpha_product_ext[UPDATE_PRODUCT_WIDTH:DATA_WIDTH];
    assign value_update_ext = {value_signed[DATA_WIDTH-1], value_signed} + alpha_scaled_ext;
    assign updated_value_slice = value_update_ext[DATA_WIDTH-1:0];
    assign _unused_td_error_high_bits = ^td_error_ext[TD_EXT_WIDTH-1:DATA_WIDTH];
    assign _unused_alpha_product_low_bits = ^alpha_product_ext[DATA_WIDTH-1:0];
    assign td_error_o = td_error_sliced;
    assign updated_value_o = updated_value_slice;
  // SR2FPGA_BEHAVIOR_END
endmodule
