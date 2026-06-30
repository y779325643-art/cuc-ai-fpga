module observation_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] obs0,
    input wire [DATA_WIDTH-1:0] obs1,
    output reg out_valid,
    input wire out_ready,
    output reg [DATA_WIDTH-1:0] obs0_out,
    output reg [DATA_WIDTH-1:0] obs1_out
);

  assign in_ready = !out_valid || out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      obs0_out <= {DATA_WIDTH{1'b0}};
      obs1_out <= {DATA_WIDTH{1'b0}};
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        obs0_out <= obs0;
        obs1_out <= obs1;
      end
    end
  end

endmodule
