module batch_result_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire out_ready,
    input wire selected_action_a,
    input wire [DATA_WIDTH-1:0] value_estimate_a,
    input wire [DATA_WIDTH-1:0] updated_value_a,
    input wire selected_action_b,
    input wire [DATA_WIDTH-1:0] value_estimate_b,
    input wire [DATA_WIDTH-1:0] updated_value_b,
    input wire done_a,
    input wire done_b,
    output reg result_valid,
    input wire result_ready,
    output reg selected_action_a_out,
    output reg [DATA_WIDTH-1:0] value_estimate_a_out,
    output reg [DATA_WIDTH-1:0] updated_value_a_out,
    output reg selected_action_b_out,
    output reg [DATA_WIDTH-1:0] value_estimate_b_out,
    output reg [DATA_WIDTH-1:0] updated_value_b_out,
    output reg batch_done_out,
    output reg irq
);

  assign out_ready = !result_valid || result_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      result_valid <= 1'b0;
      selected_action_a_out <= 1'b0;
      value_estimate_a_out <= {DATA_WIDTH{1'b0}};
      updated_value_a_out <= {DATA_WIDTH{1'b0}};
      selected_action_b_out <= 1'b0;
      value_estimate_b_out <= {DATA_WIDTH{1'b0}};
      updated_value_b_out <= {DATA_WIDTH{1'b0}};
      batch_done_out <= 1'b0;
      irq <= 1'b0;
    end else begin
      if (result_valid && result_ready) begin
        if (batch_done_out) begin
          irq <= 1'b1;
        end
        result_valid <= 1'b0;
      end
      if (in_valid && out_ready) begin
        result_valid <= 1'b1;
        selected_action_a_out <= selected_action_a;
        value_estimate_a_out <= value_estimate_a;
        updated_value_a_out <= updated_value_a;
        selected_action_b_out <= selected_action_b;
        value_estimate_b_out <= value_estimate_b;
        updated_value_b_out <= updated_value_b;
        batch_done_out <= done_a | done_b;
      end
    end
  end

endmodule
