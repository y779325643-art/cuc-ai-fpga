module batch_sample_buffer #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] obs0_a,
    input wire [DATA_WIDTH-1:0] obs1_a,
    input wire [DATA_WIDTH-1:0] reward_a,
    input wire [DATA_WIDTH-1:0] next_value_a,
    input wire done_a,
    input wire [DATA_WIDTH-1:0] obs0_b,
    input wire [DATA_WIDTH-1:0] obs1_b,
    input wire [DATA_WIDTH-1:0] reward_b,
    input wire [DATA_WIDTH-1:0] next_value_b,
    input wire done_b,
    input wire consume_ready,
    output wire out_valid,
    output reg [DATA_WIDTH-1:0] obs0_a_out,
    output reg [DATA_WIDTH-1:0] obs1_a_out,
    output reg [DATA_WIDTH-1:0] reward_a_out,
    output reg [DATA_WIDTH-1:0] next_value_a_out,
    output reg done_a_out,
    output reg [DATA_WIDTH-1:0] obs0_b_out,
    output reg [DATA_WIDTH-1:0] obs1_b_out,
    output reg [DATA_WIDTH-1:0] reward_b_out,
    output reg [DATA_WIDTH-1:0] next_value_b_out,
    output reg done_b_out
);

  reg valid_reg;

  assign in_ready = !valid_reg || consume_ready;
  assign out_valid = valid_reg;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_reg <= 1'b0;
      obs0_a_out <= {DATA_WIDTH{1'b0}};
      obs1_a_out <= {DATA_WIDTH{1'b0}};
      reward_a_out <= {DATA_WIDTH{1'b0}};
      next_value_a_out <= {DATA_WIDTH{1'b0}};
      done_a_out <= 1'b0;
      obs0_b_out <= {DATA_WIDTH{1'b0}};
      obs1_b_out <= {DATA_WIDTH{1'b0}};
      reward_b_out <= {DATA_WIDTH{1'b0}};
      next_value_b_out <= {DATA_WIDTH{1'b0}};
      done_b_out <= 1'b0;
    end else begin
      if (in_valid && in_ready) begin
        valid_reg <= 1'b1;
        obs0_a_out <= obs0_a;
        obs1_a_out <= obs1_a;
        reward_a_out <= reward_a;
        next_value_a_out <= next_value_a;
        done_a_out <= done_a;
        obs0_b_out <= obs0_b;
        obs1_b_out <= obs1_b;
        reward_b_out <= reward_b;
        next_value_b_out <= next_value_b;
        done_b_out <= done_b;
      end else if (consume_ready) begin
        valid_reg <= 1'b0;
      end
    end
  end

endmodule
