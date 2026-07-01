module fir_filter_core #(
    parameter WIDTH = 8,
    parameter RESULT_WIDTH = 11
) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid,
    input wire [WIDTH-1:0] sample,
    output reg result_valid,
    output reg [RESULT_WIDTH-1:0] result
);

  reg [WIDTH-1:0] sample_d0;
  reg [WIDTH-1:0] sample_d1;
  wire [RESULT_WIDTH-1:0] stage0;
  wire [RESULT_WIDTH-1:0] stage1;
  wire [RESULT_WIDTH-1:0] filtered_result;

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_new_sample (
    .sample(sample),
    .coefficient(2'd1),
    .accum({RESULT_WIDTH{1'b0}}),
    .result(stage0)
  );

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_previous_sample (
    .sample(sample_d0),
    .coefficient(2'd2),
    .accum(stage0),
    .result(stage1)
  );

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_oldest_sample (
    .sample(sample_d1),
    .coefficient(2'd1),
    .accum(stage1),
    .result(filtered_result)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sample_d0 <= {WIDTH{1'b0}};
      sample_d1 <= {WIDTH{1'b0}};
      result_valid <= 1'b0;
      result <= {RESULT_WIDTH{1'b0}};
    end else begin
      result_valid <= sample_valid;
      if (sample_valid) begin
        result <= filtered_result;
        sample_d1 <= sample_d0;
        sample_d0 <= sample;
      end
    end
  end

endmodule
