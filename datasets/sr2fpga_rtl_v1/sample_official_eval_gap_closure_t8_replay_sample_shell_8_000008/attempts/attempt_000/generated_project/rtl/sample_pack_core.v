module sample_pack_core #(
    parameter DATA_WIDTH = 8
) (
    input wire [DATA_WIDTH-1:0] state,
    input wire action,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] next_state,
    input wire done,
    output wire [DATA_WIDTH-1:0] sample_state,
    output wire sample_action,
    output wire [DATA_WIDTH-1:0] sample_reward,
    output wire [DATA_WIDTH-1:0] sample_next_state,
    output wire sample_done
);

  assign sample_state = state;
  assign sample_action = action;
  assign sample_reward = reward;
  assign sample_next_state = next_state;
  assign sample_done = done;

endmodule
