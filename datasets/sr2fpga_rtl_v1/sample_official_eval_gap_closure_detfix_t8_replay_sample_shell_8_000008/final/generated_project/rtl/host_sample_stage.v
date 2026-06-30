module host_sample_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] state,
    input wire action,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] next_state,
    input wire done,
    output reg out_valid,
    input wire out_ready,
    output reg [DATA_WIDTH-1:0] state_out,
    output reg action_out,
    output reg [DATA_WIDTH-1:0] reward_out,
    output reg [DATA_WIDTH-1:0] next_state_out,
    output reg done_out
);

  assign in_ready = !out_valid || out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      state_out <= {DATA_WIDTH{1'b0}};
      action_out <= 1'b0;
      reward_out <= {DATA_WIDTH{1'b0}};
      next_state_out <= {DATA_WIDTH{1'b0}};
      done_out <= 1'b0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        state_out <= state;
        action_out <= action;
        reward_out <= reward;
        next_state_out <= next_state;
        done_out <= done;
      end
    end
  end

endmodule
