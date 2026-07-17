module td_input_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire signed [DATA_WIDTH-1:0] reward,
    input wire signed [DATA_WIDTH-1:0] value,
    input wire signed [DATA_WIDTH-1:0] next_value,
    input wire [DATA_WIDTH-1:0] gamma,
    input wire [DATA_WIDTH-1:0] alpha,
    output reg out_valid,
    input wire out_ready,
    output reg signed [DATA_WIDTH-1:0] reward_out,
    output reg signed [DATA_WIDTH-1:0] value_out,
    output reg signed [DATA_WIDTH-1:0] next_value_out,
    output reg [DATA_WIDTH-1:0] gamma_out,
    output reg [DATA_WIDTH-1:0] alpha_out
);

  assign in_ready = !out_valid || out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      reward_out <= {DATA_WIDTH{1'b0}};
      value_out <= {DATA_WIDTH{1'b0}};
      next_value_out <= {DATA_WIDTH{1'b0}};
      gamma_out <= {DATA_WIDTH{1'b0}};
      alpha_out <= {DATA_WIDTH{1'b0}};
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        reward_out <= reward;
        value_out <= value;
        next_value_out <= next_value;
        gamma_out <= gamma;
        alpha_out <= alpha;
      end
    end
  end

endmodule
