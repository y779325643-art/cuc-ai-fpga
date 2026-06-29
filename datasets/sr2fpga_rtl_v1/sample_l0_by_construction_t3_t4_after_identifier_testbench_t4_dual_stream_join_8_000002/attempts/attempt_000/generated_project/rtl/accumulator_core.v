module accumulator_core #(parameter SAMPLE_WIDTH = 8, parameter SUM_WIDTH = 8) (
    input wire [None-1:0] clk,
    input wire [None-1:0] rst_n,
    input wire [None-1:0] sample_valid,
    input wire [SAMPLE_WIDTH-1:0] sample,
    output wire [None-1:0] sample_ready,
    output wire [SUM_WIDTH-1:0] sum
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    localparam IDLE   = 1'b0;
    localparam ADDING = 1'b1;
    reg [SUM_WIDTH-1:0] sum_reg;
    reg                  state;

    assign sum = sum_reg;
    assign sample_ready = 1'b1;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        sum_reg <= {SUM_WIDTH{1'b0}};
        state   <= IDLE;
      end else begin
        if (sample_valid && sample_ready) begin
          sum_reg <= sum_reg + sample;
          state   <= ADDING;
        end else begin
          state <= IDLE;
        end
      end
    end
endmodule
