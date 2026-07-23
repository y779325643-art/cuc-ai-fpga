module result_stream_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire out_ready,
    input wire selected_action,
    input wire [DATA_WIDTH-1:0] value_estimate,
    input wire [DATA_WIDTH-1:0] updated_value,
    input wire done_in,
    output reg result_valid,
    input wire result_ready,
    output reg selected_action_out,
    output reg [DATA_WIDTH-1:0] value_estimate_out,
    output reg [DATA_WIDTH-1:0] updated_value_out,
    output reg episode_done_out,
    output reg irq
);

  assign out_ready = !result_valid || result_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      result_valid <= 1'b0;
      selected_action_out <= 1'b0;
      value_estimate_out <= {DATA_WIDTH{1'b0}};
      updated_value_out <= {DATA_WIDTH{1'b0}};
      episode_done_out <= 1'b0;
      irq <= 1'b0;
    end else begin
      if (result_valid && result_ready) begin
        if (episode_done_out) begin
          irq <= 1'b1;
        end
        result_valid <= 1'b0;
      end
      if (in_valid && out_ready) begin
        result_valid <= 1'b1;
        selected_action_out <= selected_action;
        value_estimate_out <= value_estimate;
        updated_value_out <= updated_value;
        episode_done_out <= done_in && 1'b0;
      end
    end
  end

endmodule
