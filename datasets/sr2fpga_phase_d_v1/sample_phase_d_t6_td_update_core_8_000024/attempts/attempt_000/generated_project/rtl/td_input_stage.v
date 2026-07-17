module td_input_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] value,
    input wire [DATA_WIDTH-1:0] next_value,
    output wire tuple_valid,
    output wire [DATA_WIDTH-1:0] tuple_reward,
    output wire [DATA_WIDTH-1:0] tuple_value,
    output wire [DATA_WIDTH-1:0] tuple_next_value
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  reg  tuple_valid_reg;
  reg  [DATA_WIDTH-1:0] reward_reg, value_reg, next_value_reg;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tuple_valid_reg <= 1'b0;
      reward_reg      <= {DATA_WIDTH{1'b0}};
      value_reg       <= {DATA_WIDTH{1'b0}};
      next_value_reg  <= {DATA_WIDTH{1'b0}};
    end else begin
      if (in_valid && in_ready) begin
        reward_reg     <= reward;
        value_reg      <= value;
        next_value_reg <= next_value;
        tuple_valid_reg <= 1'b1;
      end else begin
        tuple_valid_reg <= 1'b0;
      end
    end
  end
  assign in_ready            = !tuple_valid_reg;
  assign tuple_valid         = tuple_valid_reg;
  assign tuple_reward        = reward_reg;
  assign tuple_value         = value_reg;
  assign tuple_next_value    = next_value_reg;
  // SR2FPGA_BEHAVIOR_END
endmodule
