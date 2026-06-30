module sample_packet_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] sample_state,
    input wire sample_action,
    input wire [DATA_WIDTH-1:0] sample_reward,
    input wire [DATA_WIDTH-1:0] sample_next_state,
    input wire sample_done,
    output reg sample_valid,
    input wire sample_ready,
    output reg [DATA_WIDTH-1:0] sample_state_out,
    output reg sample_action_out,
    output reg [DATA_WIDTH-1:0] sample_reward_out,
    output reg [DATA_WIDTH-1:0] sample_next_state_out,
    output reg sample_done_out,
    output reg irq
);

  assign in_ready = !sample_valid || sample_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sample_valid <= 1'b0;
      sample_state_out <= {DATA_WIDTH{1'b0}};
      sample_action_out <= 1'b0;
      sample_reward_out <= {DATA_WIDTH{1'b0}};
      sample_next_state_out <= {DATA_WIDTH{1'b0}};
      sample_done_out <= 1'b0;
      irq <= 1'b0;
    end else begin
      if (sample_valid && sample_ready) begin
        irq <= 1'b1;
        sample_valid <= 1'b0;
      end
      if (in_valid && in_ready) begin
        sample_valid <= 1'b1;
        sample_state_out <= sample_state;
        sample_action_out <= sample_action;
        sample_reward_out <= sample_reward;
        sample_next_state_out <= sample_next_state;
        sample_done_out <= sample_done;
      end
    end
  end

endmodule
