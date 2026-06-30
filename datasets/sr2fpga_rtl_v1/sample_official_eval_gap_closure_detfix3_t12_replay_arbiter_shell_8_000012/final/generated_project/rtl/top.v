module top (
    input wire clk,
    input wire rst_n,
    input wire host_valid,
    output wire host_ready,
    input wire [7:0] host_state,
    input wire host_action,
    input wire [7:0] host_reward,
    input wire [7:0] host_next_state,
    input wire host_done,
    input wire sample_req_valid,
    output wire sample_req_ready,
    input wire [1:0] sample_index,
    output wire sample_valid,
    input wire sample_ready,
    output wire [7:0] sample_state,
    output wire sample_action,
    output wire [7:0] sample_reward,
    output wire [7:0] sample_next_state,
    output wire sample_done,
    output wire [2:0] occupancy,
    output wire [1:0] write_index,
    output wire irq
);

  wire packet_valid;
  wire packet_ready;
  wire [7:0] packet_state;
  wire packet_action;
  wire [7:0] packet_reward;
  wire [7:0] packet_next_state;
  wire packet_done;
  wire mem_write_valid;
  wire [1:0] mem_write_addr;
  wire [7:0] mem_write_state;
  wire mem_write_action;
  wire [7:0] mem_write_reward;
  wire [7:0] mem_write_next_state;
  wire mem_write_done;
  wire mem_read_valid;
  wire [1:0] mem_read_addr;
  wire write_accepted;
  wire read_valid_out;
  wire [7:0] read_state;
  wire read_action;
  wire [7:0] read_reward;
  wire [7:0] read_next_state;
  wire read_done;
  wire sample_stage_ready;

  host_transition_packetizer #(
    .DATA_WIDTH(8)
  ) u_host_transition_packetizer (
    .host_valid(host_valid),
    .host_ready(host_ready),
    .host_state(host_state),
    .host_action(host_action),
    .host_reward(host_reward),
    .host_next_state(host_next_state),
    .host_done(host_done),
    .packet_ready(packet_ready),
    .packet_valid(packet_valid),
    .packet_state(packet_state),
    .packet_action(packet_action),
    .packet_reward(packet_reward),
    .packet_next_state(packet_next_state),
    .packet_done(packet_done)
  );

  replay_index_allocator u_replay_index_allocator (
    .clk(clk),
    .rst_n(rst_n),
    .write_accepted(write_accepted),
    .write_index(write_index),
    .occupancy(occupancy)
  );

  replay_request_arbiter #(
    .DATA_WIDTH(8)
  ) u_replay_request_arbiter (
    .write_valid(packet_valid),
    .write_ready(packet_ready),
    .write_index(write_index),
    .occupancy(occupancy),
    .write_state(packet_state),
    .write_action(packet_action),
    .write_reward(packet_reward),
    .write_next_state(packet_next_state),
    .write_done(packet_done),
    .read_req_valid(sample_req_valid),
    .sample_index(sample_index),
    .sample_stage_ready(sample_stage_ready),
    .sample_req_ready(sample_req_ready),
    .mem_write_valid(mem_write_valid),
    .mem_write_addr(mem_write_addr),
    .mem_write_state(mem_write_state),
    .mem_write_action(mem_write_action),
    .mem_write_reward(mem_write_reward),
    .mem_write_next_state(mem_write_next_state),
    .mem_write_done(mem_write_done),
    .mem_read_valid(mem_read_valid),
    .mem_read_addr(mem_read_addr),
    .write_accepted(write_accepted)
  );

  replay_memory_bank #(
    .DATA_WIDTH(8)
  ) u_replay_memory_bank (
    .clk(clk),
    .rst_n(rst_n),
    .write_valid(mem_write_valid),
    .write_addr(mem_write_addr),
    .write_state(mem_write_state),
    .write_action(mem_write_action),
    .write_reward(mem_write_reward),
    .write_next_state(mem_write_next_state),
    .write_done(mem_write_done),
    .read_valid(mem_read_valid),
    .read_addr(mem_read_addr),
    .read_valid_out(read_valid_out),
    .read_state(read_state),
    .read_action(read_action),
    .read_reward(read_reward),
    .read_next_state(read_next_state),
    .read_done(read_done)
  );

  sample_packet_stage #(
    .DATA_WIDTH(8)
  ) u_sample_packet_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(read_valid_out),
    .in_ready(sample_stage_ready),
    .sample_state(read_state),
    .sample_action(read_action),
    .sample_reward(read_reward),
    .sample_next_state(read_next_state),
    .sample_done(read_done),
    .sample_valid(sample_valid),
    .sample_ready(sample_ready),
    .sample_state_out(sample_state),
    .sample_action_out(sample_action),
    .sample_reward_out(sample_reward),
    .sample_next_state_out(sample_next_state),
    .sample_done_out(sample_done),
    .irq(irq)
  );

endmodule
