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
    reg valid_reg;
    reg [DATA_WIDTH-1:0] reward_reg, value_reg, next_value_reg, gamma_reg, alpha_reg;
    assign in_ready = !valid_reg;
    assign out_valid = valid_reg;
    assign reward_out = reward_reg;
    assign value_out = value_reg;
    assign next_value_out = next_value_reg;
    assign gamma_out = gamma_reg;
    assign alpha_out = alpha_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        valid_reg <= 1'b0;
        reward_reg <= {DATA_WIDTH{1'b0}};
        value_reg <= {DATA_WIDTH{1'b0}};
        next_value_reg <= {DATA_WIDTH{1'b0}};
        gamma_reg <= {DATA_WIDTH{1'b0}};
        alpha_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        if (in_valid && in_ready) begin
          valid_reg <= 1'b1;
          reward_reg <= reward;
          value_reg <= value;
          next_value_reg <= next_value;
          gamma_reg <= gamma;
          alpha_reg <= alpha;
        end else if (valid_reg && out_ready) begin
          valid_reg <= 1'b0;
        end
      end
    end
endmodule
