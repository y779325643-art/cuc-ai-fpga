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
    output wire sample_valid,
    input wire sample_ready,
    output wire [7:0] sample_state,
    output wire sample_action,
    output wire [7:0] sample_reward,
    output wire [7:0] sample_next_state,
    output wire sample_done,
    output wire [2:0] occupancy
);

  wire host_stage_valid;
  wire host_stage_ready;
  wire [7:0] host_stage_state;
  wire host_stage_action;
  wire [7:0] host_stage_reward;
  wire [7:0] host_stage_next_state;
  wire host_stage_done;
  wire store_read_valid;
  wire store_read_ready;
  wire [7:0] store_read_state;
  wire store_read_action;
  wire [7:0] store_read_reward;
  wire [7:0] store_read_next_state;
  wire store_read_done;
  wire [7:0] sample_pack_state;
  wire sample_pack_action;
  wire [7:0] sample_pack_reward;
  wire [7:0] sample_pack_next_state;
  wire sample_pack_done;
  wire [2:0] store_occupancy;

  host_sample_stage #(
    .DATA_WIDTH(8)
  ) u_host_sample_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(host_valid),
    .in_ready(host_ready),
    .state(host_state),
    .action(host_action),
    .reward(host_reward),
    .next_state(host_next_state),
    .done(host_done),
    .out_valid(host_stage_valid),
    .out_ready(host_stage_ready),
    .state_out(host_stage_state),
    .action_out(host_stage_action),
    .reward_out(host_stage_reward),
    .next_state_out(host_stage_next_state),
    .done_out(host_stage_done)
  );

  replay_store #(
    .DATA_WIDTH(8),
    .DEPTH(4)
  ) u_replay_store (
    .clk(clk),
    .rst_n(rst_n),
    .write_valid(host_stage_valid),
    .write_ready(host_stage_ready),
    .write_state(host_stage_state),
    .write_action(host_stage_action),
    .write_reward(host_stage_reward),
    .write_next_state(host_stage_next_state),
    .write_done(host_stage_done),
    .read_valid(store_read_valid),
    .read_ready(store_read_ready),
    .read_state(store_read_state),
    .read_action(store_read_action),
    .read_reward(store_read_reward),
    .read_next_state(store_read_next_state),
    .read_done(store_read_done),
    .occupancy(store_occupancy)
  );

  sample_pack_core #(
    .DATA_WIDTH(8)
  ) u_sample_pack_core (
    .state(store_read_state),
    .action(store_read_action),
    .reward(store_read_reward),
    .next_state(store_read_next_state),
    .done(store_read_done),
    .sample_state(sample_pack_state),
    .sample_action(sample_pack_action),
    .sample_reward(sample_pack_reward),
    .sample_next_state(sample_pack_next_state),
    .sample_done(sample_pack_done)
  );

  sample_read_stage #(
    .DATA_WIDTH(8)
  ) u_sample_read_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(store_read_valid),
    .read_ready(store_read_ready),
    .sample_state(sample_pack_state),
    .sample_action(sample_pack_action),
    .sample_reward(sample_pack_reward),
    .sample_next_state(sample_pack_next_state),
    .sample_done(sample_pack_done),
    .out_valid(sample_valid),
    .out_ready(sample_ready),
    .sample_state_out(sample_state),
    .sample_action_out(sample_action),
    .sample_reward_out(sample_reward),
    .sample_next_state_out(sample_next_state),
    .sample_done_out(sample_done)
  );

  occupancy_counter u_occupancy_counter (
    .occupancy_in(store_occupancy),
    .occupancy_out(occupancy)
  );

endmodule
