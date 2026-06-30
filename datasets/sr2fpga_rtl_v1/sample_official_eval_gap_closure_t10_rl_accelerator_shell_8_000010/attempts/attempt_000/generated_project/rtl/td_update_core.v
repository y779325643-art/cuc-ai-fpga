module td_update_core #(
    parameter DATA_WIDTH = 8
) (
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] next_value,
    input wire [DATA_WIDTH-1:0] value_estimate,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] updated_value
);

  wire [DATA_WIDTH:0] td_error_full;
  wire [(2*DATA_WIDTH)-1:0] update_product;
  wire [DATA_WIDTH-1:0] update_delta;

  assign td_error_full = {1'b0, reward} + {1'b0, next_value} - {1'b0, value_estimate};
  assign update_product = alpha * td_error_full[DATA_WIDTH-1:0];
  assign update_delta = update_product[(2*DATA_WIDTH)-1:4];
  assign updated_value = value_estimate + update_delta;
  assign out_valid = in_valid;

endmodule
