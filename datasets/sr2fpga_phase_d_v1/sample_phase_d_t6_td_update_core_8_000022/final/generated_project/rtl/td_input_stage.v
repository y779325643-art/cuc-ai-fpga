module td_input_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] reward_i,
    input wire [DATA_WIDTH-1:0] value_i,
    input wire [DATA_WIDTH-1:0] next_value_i,
    input wire [DATA_WIDTH-1:0] gamma_i,
    input wire [DATA_WIDTH-1:0] alpha_i,
    output wire tuple_valid_o,
    input wire tuple_ready_i,
    output wire [DATA_WIDTH-1:0] reward_o,
    output wire [DATA_WIDTH-1:0] value_o,
    output wire [DATA_WIDTH-1:0] next_value_o,
    output wire [DATA_WIDTH-1:0] gamma_o,
    output wire [DATA_WIDTH-1:0] alpha_o
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] input_reward_reg;
    reg [DATA_WIDTH-1:0] input_value_reg;
    reg [DATA_WIDTH-1:0] input_next_value_reg;
    reg [DATA_WIDTH-1:0] input_gamma_reg;
    reg [DATA_WIDTH-1:0] input_alpha_reg;
    reg input_tuple_valid_reg;

    wire input_can_accept;

    assign input_can_accept = (!input_tuple_valid_reg) || tuple_ready_i;
    assign in_ready = input_can_accept;
    assign tuple_valid_o = input_tuple_valid_reg;
    assign reward_o = input_reward_reg;
    assign value_o = input_value_reg;
    assign next_value_o = input_next_value_reg;
    assign gamma_o = input_gamma_reg;
    assign alpha_o = input_alpha_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        input_reward_reg <= {DATA_WIDTH{1'b0}};
        input_value_reg <= {DATA_WIDTH{1'b0}};
        input_next_value_reg <= {DATA_WIDTH{1'b0}};
        input_gamma_reg <= {DATA_WIDTH{1'b0}};
        input_alpha_reg <= {DATA_WIDTH{1'b0}};
        input_tuple_valid_reg <= 1'b0;
      end else begin
        if (input_can_accept) begin
          input_tuple_valid_reg <= in_valid;
          if (in_valid) begin
            input_reward_reg <= reward_i;
            input_value_reg <= value_i;
            input_next_value_reg <= next_value_i;
            input_gamma_reg <= gamma_i;
            input_alpha_reg <= alpha_i;
          end
        end
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
