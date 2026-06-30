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
    wire signed [15:0] product;
    assign product = $signed(gamma) * $signed(next_value);
    wire [DATA_WIDTH-1:0] scaled_product;
    assign scaled_product = product[SCALE_SHIFT+DATA_WIDTH-1 : SCALE_SHIFT];
    assign discounted_return = $signed(reward) + $signed(scaled_product);
    assign out_valid = in_valid;
    assign in_ready = out_ready;
endmodule
