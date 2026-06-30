module policy_value_core #(
    parameter DATA_WIDTH = 8
) (
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] obs0,
    input wire [DATA_WIDTH-1:0] obs1,
    input wire [DATA_WIDTH-1:0] weight0,
    input wire [DATA_WIDTH-1:0] bias0,
    input wire [DATA_WIDTH-1:0] weight1,
    input wire [DATA_WIDTH-1:0] bias1,
    input wire enable,
    output wire out_valid,
    output wire selected_action,
    output wire [DATA_WIDTH-1:0] value_estimate
);

  wire [(2*DATA_WIDTH):0] score0_full;
  wire [(2*DATA_WIDTH):0] score1_full;
  wire [DATA_WIDTH-1:0] score0;
  wire [DATA_WIDTH-1:0] score1;
  wire [DATA_WIDTH:0] value_sum;

  assign score0_full = (obs0 * weight0) + bias0;
  assign score1_full = (obs1 * weight1) + bias1;
  assign score0 = score0_full[DATA_WIDTH-1:0];
  assign score1 = score1_full[DATA_WIDTH-1:0];
  assign value_sum = {1'b0, score0} + {1'b0, score1};
  assign selected_action = score1 > score0;
  assign value_estimate = value_sum[DATA_WIDTH:1];
  assign out_valid = in_valid && enable;

endmodule
