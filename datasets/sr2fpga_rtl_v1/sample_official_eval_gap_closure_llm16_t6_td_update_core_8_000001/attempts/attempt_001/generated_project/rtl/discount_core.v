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
    wire [15:0] mult;
    wire [3:0] _unused_mult_low;
    wire [8:0] sum;
    wire _unused_sum_high;
    assign mult = next_value * gamma;
    assign _unused_mult_low = mult[3:0];
    assign sum = {1'b0, reward} + {1'b0, mult[11:4]};
    assign _unused_sum_high = sum[8];
    assign discounted_return = sum[7:0];
    assign out_valid = in_valid;
    assign in_ready = out_ready;
endmodule
