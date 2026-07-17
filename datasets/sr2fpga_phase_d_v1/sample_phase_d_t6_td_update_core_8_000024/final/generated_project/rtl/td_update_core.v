module td_update_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] value,
    input wire [DATA_WIDTH-1:0] discounted_value,
    input wire [DATA_WIDTH-1:0] alpha,
    output wire [DATA_WIDTH-1:0] td_error,
    output wire [DATA_WIDTH-1:0] updated_value
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  wire signed [DATA_WIDTH-1:0] s_reward          = reward;
  wire signed [DATA_WIDTH-1:0] s_discounted_value = discounted_value;
  wire signed [DATA_WIDTH-1:0] s_value           = value;
  wire signed [DATA_WIDTH-1:0] s_alpha           = alpha;

  wire signed [DATA_WIDTH:0] td_error_ext = {s_reward[DATA_WIDTH-1], s_reward} + 
                                             {s_discounted_value[DATA_WIDTH-1], s_discounted_value} - 
                                             {s_value[DATA_WIDTH-1], s_value};
  assign td_error = td_error_ext[DATA_WIDTH-1:0];

  wire signed [2*DATA_WIDTH-1:0] alpha_td_product = s_alpha * $signed(td_error);
  wire signed [DATA_WIDTH:0]     updated_ext = {s_value[DATA_WIDTH-1], s_value} + 
                                               $signed({alpha_td_product[DATA_WIDTH-1], alpha_td_product[DATA_WIDTH-1:0]});
  assign updated_value = updated_ext[DATA_WIDTH-1:0];

  always @* begin
    if (alpha_td_product[2*DATA_WIDTH-1:DATA_WIDTH] != 0) begin
    end
  end
  // SR2FPGA_BEHAVIOR_END
endmodule
