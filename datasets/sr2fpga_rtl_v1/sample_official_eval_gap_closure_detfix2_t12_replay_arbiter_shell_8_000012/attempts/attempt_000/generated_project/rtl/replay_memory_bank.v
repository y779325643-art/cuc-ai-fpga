module replay_memory_bank #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire write_valid,
    input wire [1:0] write_addr,
    input wire [DATA_WIDTH-1:0] write_state,
    input wire write_action,
    input wire [DATA_WIDTH-1:0] write_reward,
    input wire [DATA_WIDTH-1:0] write_next_state,
    input wire write_done,
    input wire read_valid,
    input wire [1:0] read_addr,
    output reg read_valid_out,
    output reg [DATA_WIDTH-1:0] read_state,
    output reg read_action,
    output reg [DATA_WIDTH-1:0] read_reward,
    output reg [DATA_WIDTH-1:0] read_next_state,
    output reg read_done
);

  reg [DATA_WIDTH-1:0] state_mem [0:3];
  reg action_mem [0:3];
  reg [DATA_WIDTH-1:0] reward_mem [0:3];
  reg [DATA_WIDTH-1:0] next_state_mem [0:3];
  reg done_mem [0:3];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      read_valid_out <= 1'b0;
      read_state <= {DATA_WIDTH{1'b0}};
      read_action <= 1'b0;
      read_reward <= {DATA_WIDTH{1'b0}};
      read_next_state <= {DATA_WIDTH{1'b0}};
      read_done <= 1'b0;
    end else begin
      read_valid_out <= read_valid;
      if (write_valid) begin
        state_mem[write_addr] <= write_state;
        action_mem[write_addr] <= write_action;
        reward_mem[write_addr] <= write_reward;
        next_state_mem[write_addr] <= write_next_state;
        done_mem[write_addr] <= write_done;
      end
      if (read_valid) begin
        read_state <= state_mem[read_addr];
        read_action <= action_mem[read_addr];
        read_reward <= reward_mem[read_addr];
        read_next_state <= next_state_mem[read_addr];
        read_done <= done_mem[read_addr];
      end
    end
  end

endmodule
