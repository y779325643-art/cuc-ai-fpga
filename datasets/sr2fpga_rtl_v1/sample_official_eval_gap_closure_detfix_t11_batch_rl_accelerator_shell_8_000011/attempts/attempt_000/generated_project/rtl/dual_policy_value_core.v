module dual_policy_value_core #(
    parameter DATA_WIDTH = 8
) (
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] obs0_a,
    input wire [DATA_WIDTH-1:0] obs1_a,
    input wire [DATA_WIDTH-1:0] obs0_b,
    input wire [DATA_WIDTH-1:0] obs1_b,
    input wire [DATA_WIDTH-1:0] weight0,
    input wire [DATA_WIDTH-1:0] bias0,
    input wire [DATA_WIDTH-1:0] weight1,
    input wire [DATA_WIDTH-1:0] bias1,
    input wire enable,
    output wire out_valid,
    output wire selected_action_a,
    output wire [DATA_WIDTH-1:0] value_estimate_a,
    output wire selected_action_b,
    output wire [DATA_WIDTH-1:0] value_estimate_b
);

  wire [(2*DATA_WIDTH)-1:0] score0_a_full;
  wire [(2*DATA_WIDTH)-1:0] score1_a_full;
  wire [(2*DATA_WIDTH)-1:0] score0_b_full;
  wire [(2*DATA_WIDTH)-1:0] score1_b_full;
  wire [DATA_WIDTH-1:0] score0_a;
  wire [DATA_WIDTH-1:0] score1_a;
  wire [DATA_WIDTH-1:0] score0_b;
  wire [DATA_WIDTH-1:0] score1_b;
  wire [DATA_WIDTH:0] value_sum_a;
  wire [DATA_WIDTH:0] value_sum_b;
  wire average_discard_a;
  wire average_discard_b;

  assign score0_a_full = (obs0_a * weight0) + {{DATA_WIDTH{1'b0}}, bias0};
  assign score1_a_full = (obs1_a * weight1) + {{DATA_WIDTH{1'b0}}, bias1};
  assign score0_b_full = (obs0_b * weight0) + {{DATA_WIDTH{1'b0}}, bias0};
  assign score1_b_full = (obs1_b * weight1) + {{DATA_WIDTH{1'b0}}, bias1};
  assign score0_a = |score0_a_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                    score0_a_full[DATA_WIDTH-1:0];
  assign score1_a = |score1_a_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                    score1_a_full[DATA_WIDTH-1:0];
  assign score0_b = |score0_b_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                    score0_b_full[DATA_WIDTH-1:0];
  assign score1_b = |score1_b_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                    score1_b_full[DATA_WIDTH-1:0];
  assign value_sum_a = {1'b0, score0_a} + {1'b0, score1_a};
  assign value_sum_b = {1'b0, score0_b} + {1'b0, score1_b};
  assign average_discard_a = value_sum_a[0];
  assign average_discard_b = value_sum_b[0];
  assign selected_action_a = (score1_a > score0_a) |
                             (average_discard_a & (score1_a > score0_a));
  assign selected_action_b = (score1_b > score0_b) |
                             (average_discard_b & (score1_b > score0_b));
  assign value_estimate_a = value_sum_a[DATA_WIDTH:1];
  assign value_estimate_b = value_sum_b[DATA_WIDTH:1];
  assign out_valid = in_valid && enable;

endmodule
