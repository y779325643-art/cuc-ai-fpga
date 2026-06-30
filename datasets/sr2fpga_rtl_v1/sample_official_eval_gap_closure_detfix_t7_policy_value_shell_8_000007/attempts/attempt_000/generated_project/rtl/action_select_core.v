module action_select_core #(
    parameter DATA_WIDTH = 8
) (
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] score0,
    input wire [DATA_WIDTH-1:0] score1,
    output wire out_valid,
    input wire out_ready,
    output wire selected_action,
    output wire [DATA_WIDTH-1:0] value_estimate
);

  wire [DATA_WIDTH:0] score_sum;
  wire average_discard;

  assign in_ready = out_ready;
  assign out_valid = in_valid;
  assign score_sum = {1'b0, score0} + {1'b0, score1};
  assign average_discard = score_sum[0];
  assign selected_action = (score1 > score0) | (average_discard & (score1 > score0));
  assign value_estimate = score_sum[DATA_WIDTH:1];

endmodule
