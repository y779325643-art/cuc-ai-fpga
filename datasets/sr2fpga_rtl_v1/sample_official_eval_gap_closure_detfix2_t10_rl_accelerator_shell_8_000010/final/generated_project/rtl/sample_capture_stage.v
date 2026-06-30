module sample_capture_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] obs0,
    input wire [DATA_WIDTH-1:0] obs1,
    input wire [DATA_WIDTH-1:0] reward,
    input wire [DATA_WIDTH-1:0] next_value,
    input wire done_in,
    input wire consume_ready,
    output wire out_valid,
    output reg [DATA_WIDTH-1:0] obs0_out,
    output reg [DATA_WIDTH-1:0] obs1_out,
    output reg [DATA_WIDTH-1:0] reward_out,
    output reg [DATA_WIDTH-1:0] next_value_out,
    output reg done_out
);

  reg valid_reg;

  assign in_ready = !valid_reg || consume_ready;
  assign out_valid = valid_reg;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_reg <= 1'b0;
      obs0_out <= {DATA_WIDTH{1'b0}};
      obs1_out <= {DATA_WIDTH{1'b0}};
      reward_out <= {DATA_WIDTH{1'b0}};
      next_value_out <= {DATA_WIDTH{1'b0}};
      done_out <= 1'b0;
    end else begin
      if (in_valid && in_ready) begin
        valid_reg <= 1'b1;
        obs0_out <= obs0;
        obs1_out <= obs1;
        reward_out <= reward;
        next_value_out <= next_value;
        done_out <= done_in;
      end else if (consume_ready) begin
        valid_reg <= 1'b0;
      end
    end
  end

endmodule
