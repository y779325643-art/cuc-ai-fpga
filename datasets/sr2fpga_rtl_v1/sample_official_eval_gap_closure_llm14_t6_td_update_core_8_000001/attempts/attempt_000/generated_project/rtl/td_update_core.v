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
    // Combinational ready/valid passthrough
    assign in_ready  = out_ready;
    assign out_valid = in_valid & out_ready;

    // Treat operands as signed
    wire signed [DATA_WIDTH-1:0] dr    = $signed(discounted_return);
    wire signed [DATA_WIDTH-1:0] v     = $signed(value);
    wire signed [DATA_WIDTH-1:0] a     = $signed(alpha);

    // TD error: discounted_return - value
    wire signed [DATA_WIDTH:0] err_ext = dr - v; // one extra bit for possible overflow

    // updated_value = value + (alpha * td_error) >>> SCALE_SHIFT
    wire signed [2*DATA_WIDTH:0] mul    = a * err_ext;  // sufficient width
    wire signed [2*DATA_WIDTH:0] scaled = mul >>> SCALE_SHIFT;
    wire signed [DATA_WIDTH:0]   new_val = v + $signed(scaled[DATA_WIDTH-1:0]);

    // Outputs (truncate to DATA_WIDTH)
    assign td_error      = err_ext[DATA_WIDTH-1:0];
    assign updated_value = new_val[DATA_WIDTH-1:0];
endmodule
