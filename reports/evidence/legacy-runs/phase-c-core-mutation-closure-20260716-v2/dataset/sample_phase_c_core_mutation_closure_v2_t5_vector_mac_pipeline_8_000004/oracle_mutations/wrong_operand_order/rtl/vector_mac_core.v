module vector_mac_core #(
    parameter DATA_WIDTH = 8,
    parameter SCORE_WIDTH = 16
) (
    input wire clk,
    input wire rst_n,
    input wire feature_valid,
    output wire feature_ready,
    input wire [DATA_WIDTH-1:0] feature_data,
    input wire weight_valid,
    output wire weight_ready,
    input wire [DATA_WIDTH-1:0] weight_data,
    input wire [SCORE_WIDTH-1:0] bias,
    output reg score_valid,
    input wire score_ready,
    output reg [SCORE_WIDTH-1:0] score_data
);

  reg signed [SCORE_WIDTH-1:0] accumulator;
  reg [1:0] vector_index;
  localparam [1:0] LAST_INDEX = 2'd3;
  wire accept_pair;
  wire signed [SCORE_WIDTH-1:0] product;
  wire signed [SCORE_WIDTH-1:0] next_accumulator;

  assign feature_ready = weight_valid && !score_valid;
  assign weight_ready = feature_valid && !score_valid;
  assign accept_pair = feature_valid && feature_ready && weight_valid && weight_ready;
  assign product = $signed(feature_data) * $signed({weight_data[DATA_WIDTH-2:0], weight_data[DATA_WIDTH-1]});
  assign next_accumulator = $signed(accumulator) + product;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      accumulator <= {SCORE_WIDTH{1'b0}};
      vector_index <= 2'd0;
      score_valid <= 1'b0;
      score_data <= {SCORE_WIDTH{1'b0}};
    end else begin
      if (score_valid && score_ready) begin
        score_valid <= 1'b0;
      end
      if (accept_pair) begin
        if (vector_index == LAST_INDEX) begin
          score_data <= next_accumulator + bias;
          score_valid <= 1'b1;
          accumulator <= {SCORE_WIDTH{1'b0}};
          vector_index <= 2'd0;
        end else begin
          accumulator <= next_accumulator;
          vector_index <= vector_index + 2'd1;
        end
      end
    end
  end

endmodule
