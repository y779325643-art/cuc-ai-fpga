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
    wire signed [15:0] product;
    wire signed [DATA_WIDTH-1:0] td_error_int;
    assign td_error_int = $signed(discounted_return) - $signed(value);
    assign td_error = td_error_int;
    assign product = $signed(alpha) * $signed(td_error_int);
    wire [DATA_WIDTH-1:0] scaled_product;
    assign scaled_product = product[SCALE_SHIFT+DATA_WIDTH-1 : SCALE_SHIFT];
    assign updated_value = $signed(value) + $signed(scaled_product);
    assign out_valid = in_valid;
    assign in_ready = out_ready;
endmodule
