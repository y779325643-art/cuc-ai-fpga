module dual_td_update_core #(
    parameter DATA_WIDTH = 8
) (
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] reward_a,
    input wire [DATA_WIDTH-1:0] next_value_a,
    input wire [DATA_WIDTH-1:0] value_estimate_a,
    input wire [DATA_WIDTH-1:0] reward_b,
    input wire [DATA_WIDTH-1:0] next_value_b,
    input wire [DATA_WIDTH-1:0] value_estimate_b,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] updated_value_a,
    output wire [DATA_WIDTH-1:0] updated_value_b
);

  wire [DATA_WIDTH:0] td_error_a_full;
  wire [DATA_WIDTH:0] td_error_b_full;
  wire [(2*DATA_WIDTH)-1:0] update_product_a;
  wire [(2*DATA_WIDTH)-1:0] update_product_b;
  wire [DATA_WIDTH-1:0] update_delta_a;
  wire [DATA_WIDTH-1:0] update_delta_b;

  assign td_error_a_full = {1'b0, reward_a} + {1'b0, next_value_a} - {1'b0, value_estimate_a};
  assign td_error_b_full = {1'b0, reward_b} + {1'b0, next_value_b} - {1'b0, value_estimate_b};
  assign update_product_a = alpha * td_error_a_full[DATA_WIDTH-1:0];
  assign update_product_b = alpha * td_error_b_full[DATA_WIDTH-1:0];
  assign update_delta_a = update_product_a[(2*DATA_WIDTH)-1:4];
  assign update_delta_b = update_product_b[(2*DATA_WIDTH)-1:4];
  assign updated_value_a = value_estimate_a + update_delta_a;
  assign updated_value_b = value_estimate_b + update_delta_b;
  assign out_valid = in_valid;

endmodule
