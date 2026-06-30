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
    reg [DATA_WIDTH-1:0] reward_r, value_r, next_value_r, gamma_r, alpha_r;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_r <= 1'b0;
        reward_r <= {DATA_WIDTH{1'b0}};
        value_r <= {DATA_WIDTH{1'b0}};
        next_value_r <= {DATA_WIDTH{1'b0}};
        gamma_r <= {DATA_WIDTH{1'b0}};
        alpha_r <= {DATA_WIDTH{1'b0}};
      end else begin
        if (in_valid && in_ready) begin
          reward_r <= reward;
          value_r <= value;
          next_value_r <= next_value;
          gamma_r <= gamma;
          alpha_r <= alpha;
          out_valid_r <= 1'b1;
        end
        if (out_valid_r && out_ready) begin
          out_valid_r <= 1'b0;
        end
      end
    end

    assign in_ready = !out_valid_r || out_ready;
    assign out_valid = out_valid_r;
    assign reward_out = reward_r;
    assign value_out = value_r;
    assign next_value_out = next_value_r;
    assign gamma_out = gamma_r;
    assign alpha_out = alpha_r;

    // tie off unused clock/reset wire to avoid synth warnings
endmodule
