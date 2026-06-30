module replay_request_arbiter #(
    parameter DATA_WIDTH = 8
) (
    input wire write_valid,
    output wire write_ready,
    input wire [1:0] write_index,
    input wire [2:0] occupancy,
    input wire [DATA_WIDTH-1:0] write_state,
    input wire write_action,
    input wire [DATA_WIDTH-1:0] write_reward,
    input wire [DATA_WIDTH-1:0] write_next_state,
    input wire write_done,
    input wire read_req_valid,
    input wire [1:0] sample_index,
    input wire sample_stage_ready,
    output wire sample_req_ready,
    output wire mem_write_valid,
    output wire [1:0] mem_write_addr,
    output wire [DATA_WIDTH-1:0] mem_write_state,
    output wire mem_write_action,
    output wire [DATA_WIDTH-1:0] mem_write_reward,
    output wire [DATA_WIDTH-1:0] mem_write_next_state,
    output wire mem_write_done,
    output wire mem_read_valid,
    output wire [1:0] mem_read_addr,
    output wire write_accepted
);

  wire read_index_valid;

  assign write_ready = 1'b1;
  assign write_accepted = write_valid && write_ready;
  assign read_index_valid = {1'b0, sample_index} < occupancy;
  assign sample_req_ready = !write_valid && read_index_valid && sample_stage_ready;
  assign mem_write_valid = write_accepted;
  assign mem_write_addr = write_index;
  assign mem_write_state = write_state;
  assign mem_write_action = write_action;
  assign mem_write_reward = write_reward;
  assign mem_write_next_state = write_next_state;
  assign mem_write_done = write_done;
  assign mem_read_valid = read_req_valid && sample_req_ready;
  assign mem_read_addr = sample_index;

endmodule
