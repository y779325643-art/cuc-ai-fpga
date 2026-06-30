module policy_score_core #(
    parameter DATA_WIDTH = 8
) (
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] obs0,
    input wire [DATA_WIDTH-1:0] obs1,
    input wire [DATA_WIDTH-1:0] weight0,
    input wire [DATA_WIDTH-1:0] weight1,
    input wire [DATA_WIDTH-1:0] bias0,
    input wire [DATA_WIDTH-1:0] bias1,
    input wire enable,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] score0,
    output wire [DATA_WIDTH-1:0] score1
);

  wire [(2*DATA_WIDTH)-1:0] score0_full;
  wire [(2*DATA_WIDTH)-1:0] score1_full;

  assign in_ready = out_ready;
  assign out_valid = in_valid;
  assign score0_full = (obs0 * weight0) + bias0;
  assign score1_full = (obs1 * weight1) + bias1;
  assign score0 = enable ? score0_full[DATA_WIDTH-1:0] : {DATA_WIDTH{1'b0}};
  assign score1 = enable ? score1_full[DATA_WIDTH-1:0] : {DATA_WIDTH{1'b0}};

endmodule
