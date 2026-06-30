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
    wire [DATA_WIDTH-1:0] error;
    wire [2*DATA_WIDTH-1:0] product;

    assign error = discounted_return - value;
    assign product = alpha * error;

    assign td_error = error;
    assign updated_value = value + (product >> SCALE_SHIFT);

    assign in_ready = out_ready;
    assign out_valid = in_valid;
endmodule
