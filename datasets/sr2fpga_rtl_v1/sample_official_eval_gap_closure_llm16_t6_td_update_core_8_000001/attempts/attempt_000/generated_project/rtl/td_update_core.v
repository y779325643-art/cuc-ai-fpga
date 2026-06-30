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
    wire signed [8:0] td_error_s;
    wire [8:0] alpha_ext;
    wire signed [17:0] mult_full;
    wire signed [17:0] mult_scaled;
    wire signed [17:0] value_ext;
    wire signed [17:0] update_sum;
    reg [7:0] updated_value_reg;
    wire _unused_td_error_high;
    wire [9:0] _unused_update_sum_high;
    wire [3:0] _unused_mult_low;
    assign td_error_s = $signed({1'b0, discounted_return}) - $signed({1'b0, value});
    assign _unused_td_error_high = td_error_s[8];
    assign td_error = td_error_s[7:0];
    assign alpha_ext = {1'b0, alpha};
    assign mult_full = $signed(alpha_ext) * td_error_s;
    assign _unused_mult_low = mult_full[3:0];
    assign mult_scaled = mult_full >>> 4;
    assign value_ext = $signed({10{1'b0}, value});
    assign update_sum = value_ext + mult_scaled;
    always @* begin
      if (update_sum <= 0)
        updated_value_reg = 8'd0;
      else if (update_sum >= 255)
        updated_value_reg = 8'd255;
      else
        updated_value_reg = update_sum[7:0];
    end
    assign updated_value = updated_value_reg;
    assign out_valid = in_valid;
    assign in_ready = out_ready;
    assign _unused_update_sum_high = update_sum[17:8];
endmodule
