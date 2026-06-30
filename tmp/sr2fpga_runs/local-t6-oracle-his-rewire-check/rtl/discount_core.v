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
    wire [2*DATA_WIDTH-1:0] product;

    assign product = gamma * next_value;
    assign discounted_return = reward + (product >> SCALE_SHIFT);

    assign in_ready = out_ready;
    assign out_valid = in_valid;
endmodule
