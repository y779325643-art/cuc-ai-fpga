module td_input_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] value,
    input wire [DATA_WIDTH-1:0] next_value,
    input wire [DATA_WIDTH-1:0] gamma,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] reward_out,
    output wire [DATA_WIDTH-1:0] value_out,
    output wire [DATA_WIDTH-1:0] next_value_out,
    output wire [DATA_WIDTH-1:0] gamma_out,
    output wire [DATA_WIDTH-1:0] alpha_out
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg out_valid_r;
    reg [DATA_WIDTH-1:0] reward_out_r, value_out_r, next_value_out_r, gamma_out_r, alpha_out_r;
    assign out_valid = out_valid_r;
    assign reward_out = reward_out_r;
    assign value_out = value_out_r;
    assign next_value_out = next_value_out_r;
    assign gamma_out = gamma_out_r;
    assign alpha_out = alpha_out_r;
    assign in_ready = out_ready | !out_valid_r;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_r <= 1'b0;
        reward_out_r <= 0;
        value_out_r <= 0;
        next_value_out_r <= 0;
        gamma_out_r <= 0;
        alpha_out_r <= 0;
      end else begin
        if (in_valid && in_ready) begin
          out_valid_r <= 1'b1;
          reward_out_r <= reward;
          value_out_r <= value;
          next_value_out_r <= next_value;
          gamma_out_r <= gamma;
          alpha_out_r <= alpha;
        end else if (out_ready && out_valid_r) begin
          out_valid_r <= 1'b0;
        end
      end
    end
endmodule
