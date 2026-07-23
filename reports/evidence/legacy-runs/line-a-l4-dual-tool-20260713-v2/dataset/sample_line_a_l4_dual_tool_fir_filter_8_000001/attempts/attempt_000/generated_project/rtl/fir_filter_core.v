module fir_filter_core #(
    parameter WIDTH = 8,
    parameter RESULT_WIDTH = 11
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

  localparam signed [2:0] COEFF_NEW = 3'sd3;
  localparam signed [2:0] COEFF_PREV = -3'sd2;
  localparam signed [2:0] COEFF_OLD = 3'sd1;

  reg signed [WIDTH-1:0] sample_d0;
  reg signed [WIDTH-1:0] sample_d1;
  wire signed [RESULT_WIDTH-1:0] stage0;
  wire signed [RESULT_WIDTH-1:0] stage1;
  wire signed [RESULT_WIDTH-1:0] filtered_result;

  assign sample_ready = !result_valid || result_ready;

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_new_sample (
    .sample(sample),
    .coefficient(COEFF_NEW),
    .accum({RESULT_WIDTH{1'b0}}),
    .result(stage0)
  );

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_previous_sample (
    .sample(sample_d0),
    .coefficient(COEFF_PREV),
    .accum(stage0),
    .result(stage1)
  );

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_oldest_sample (
    .sample(sample_d1),
    .coefficient(COEFF_OLD),
    .accum(stage1),
    .result(filtered_result)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sample_d0 <= {WIDTH{1'b0}};
      sample_d1 <= {WIDTH{1'b0}};
      result_valid <= 1'b0;
      result <= {RESULT_WIDTH{1'b0}};
    end else if (sample_ready) begin
      result_valid <= sample_valid;
      if (sample_valid) begin
        result <= filtered_result;
        sample_d1 <= sample_d0;
        sample_d0 <= sample;
      end
    end
  end

endmodule
