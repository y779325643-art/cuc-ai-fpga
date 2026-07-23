module dot_product_engine #(
    parameter WIDTH = 8,
    parameter RESULT_WIDTH = 12
) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    output wire sample_ready,
    input wire signed [WIDTH-1:0] sample,
    output reg result_valid,
    input wire result_ready,
    output reg signed [RESULT_WIDTH-1:0] result
);

  reg [1:0] index;
  reg signed [RESULT_WIDTH-1:0] accum;
  wire signed [2:0] coefficient;
  wire signed [RESULT_WIDTH-1:0] next_accum;

  assign sample_ready = !result_valid || result_ready;

  vector_rom u_vector_rom (
    .addr(index),
    .coefficient(coefficient)
  );

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_unit (
    .sample(sample),
    .coefficient(coefficient),
    .accum(accum),
    .result(next_accum)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      index <= 2'd0;
      accum <= {RESULT_WIDTH{1'b0}};
      result_valid <= 1'b0;
      result <= {RESULT_WIDTH{1'b0}};
    end else begin
      if (result_valid && result_ready) begin
        result_valid <= 1'b0;
      end
      if (sample_valid && sample_ready) begin
        if (index == 2'd3) begin
          result <= accum;
          result_valid <= 1'b1;
          index <= 2'd0;
          accum <= {RESULT_WIDTH{1'b0}};
        end else begin
          accum <= next_accum;
          index <= index + 2'd1;
        end
      end
    end
  end

endmodule
