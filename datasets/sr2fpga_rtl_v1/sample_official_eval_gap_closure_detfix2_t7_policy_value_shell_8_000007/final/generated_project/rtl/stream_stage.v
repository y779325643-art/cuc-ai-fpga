module stream_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire selected_action,
    input wire [DATA_WIDTH-1:0] value_estimate,
    output reg out_valid,
    input wire out_ready,
    output reg selected_action_out,
    output reg [DATA_WIDTH-1:0] value_estimate_out
);

  assign in_ready = !out_valid || out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      selected_action_out <= 1'b0;
      value_estimate_out <= {DATA_WIDTH{1'b0}};
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        selected_action_out <= selected_action;
        value_estimate_out <= value_estimate;
      end
    end
  end

endmodule
