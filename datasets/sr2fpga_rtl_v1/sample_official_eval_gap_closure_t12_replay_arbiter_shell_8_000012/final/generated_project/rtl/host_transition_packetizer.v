module host_transition_packetizer #(
    parameter DATA_WIDTH = 8
) (
    input wire host_valid,
    output wire host_ready,
    input wire [DATA_WIDTH-1:0] host_state,
    input wire host_action,
    input wire [DATA_WIDTH-1:0] host_reward,
    input wire [DATA_WIDTH-1:0] host_next_state,
    input wire host_done,
    input wire packet_ready,
    output wire packet_valid,
    output wire [DATA_WIDTH-1:0] packet_state,
    output wire packet_action,
    output wire [DATA_WIDTH-1:0] packet_reward,
    output wire [DATA_WIDTH-1:0] packet_next_state,
    output wire packet_done
);

  assign host_ready = packet_ready;
  assign packet_valid = host_valid && packet_ready;
  assign packet_state = host_state;
  assign packet_action = host_action;
  assign packet_reward = host_reward;
  assign packet_next_state = host_next_state;
  assign packet_done = host_done;

endmodule
