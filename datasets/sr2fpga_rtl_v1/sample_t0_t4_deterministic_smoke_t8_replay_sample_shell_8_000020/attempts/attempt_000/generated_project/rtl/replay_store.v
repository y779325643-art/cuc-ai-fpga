module replay_store #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 4
) (
    input wire clk,
    input wire rst_n,
    input wire write_valid,
    output wire write_ready,
    input wire [DATA_WIDTH-1:0] write_state,
    input wire write_action,
    input wire [DATA_WIDTH-1:0] write_reward,
    input wire [DATA_WIDTH-1:0] write_next_state,
    input wire write_done,
    output wire read_valid,
    input wire read_ready,
    output wire [DATA_WIDTH-1:0] read_state,
    output wire read_action,
    output wire [DATA_WIDTH-1:0] read_reward,
    output wire [DATA_WIDTH-1:0] read_next_state,
    output wire read_done,
    output reg [2:0] occupancy
);

  reg [DATA_WIDTH-1:0] state_mem [0:DEPTH-1];
  reg action_mem [0:DEPTH-1];
  reg [DATA_WIDTH-1:0] reward_mem [0:DEPTH-1];
  reg [DATA_WIDTH-1:0] next_state_mem [0:DEPTH-1];
  reg done_mem [0:DEPTH-1];
  reg [1:0] write_ptr;
  reg [1:0] read_ptr;
  wire write_fire;
  wire read_fire;

  assign write_ready = occupancy < 3'd4;
  assign read_valid = occupancy != 3'd0;
  assign write_fire = write_valid && write_ready;
  assign read_fire = read_valid && read_ready;
  assign read_state = state_mem[read_ptr];
  assign read_action = action_mem[read_ptr];
  assign read_reward = reward_mem[read_ptr];
  assign read_next_state = next_state_mem[read_ptr];
  assign read_done = done_mem[read_ptr];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      write_ptr <= 2'd0;
      read_ptr <= 2'd0;
      occupancy <= 3'd0;
      state_mem[0] <= {DATA_WIDTH{1'b0}};
      state_mem[1] <= {DATA_WIDTH{1'b0}};
      state_mem[2] <= {DATA_WIDTH{1'b0}};
      state_mem[3] <= {DATA_WIDTH{1'b0}};
      action_mem[0] <= 1'b0;
      action_mem[1] <= 1'b0;
      action_mem[2] <= 1'b0;
      action_mem[3] <= 1'b0;
      reward_mem[0] <= {DATA_WIDTH{1'b0}};
      reward_mem[1] <= {DATA_WIDTH{1'b0}};
      reward_mem[2] <= {DATA_WIDTH{1'b0}};
      reward_mem[3] <= {DATA_WIDTH{1'b0}};
      next_state_mem[0] <= {DATA_WIDTH{1'b0}};
      next_state_mem[1] <= {DATA_WIDTH{1'b0}};
      next_state_mem[2] <= {DATA_WIDTH{1'b0}};
      next_state_mem[3] <= {DATA_WIDTH{1'b0}};
      done_mem[0] <= 1'b0;
      done_mem[1] <= 1'b0;
      done_mem[2] <= 1'b0;
      done_mem[3] <= 1'b0;
    end else begin
      if (write_fire) begin
        state_mem[write_ptr] <= write_state;
        action_mem[write_ptr] <= write_action;
        reward_mem[write_ptr] <= write_reward;
        next_state_mem[write_ptr] <= write_next_state;
        done_mem[write_ptr] <= write_done;
        write_ptr <= write_ptr + 2'd1;
      end
      if (read_fire) begin
        read_ptr <= read_ptr + 2'd1;
      end
      if (write_fire && !read_fire) begin
        occupancy <= occupancy + 3'd1;
      end else if (!write_fire && read_fire) begin
        occupancy <= occupancy - 3'd1;
      end
    end
  end

endmodule
