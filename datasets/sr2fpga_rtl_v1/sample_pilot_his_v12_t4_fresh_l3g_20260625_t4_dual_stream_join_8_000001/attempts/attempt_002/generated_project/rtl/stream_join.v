module stream_join #(parameter W=8) (
  input clk, rst_n,
  input [W-1:0] input0_data,
  input input0_valid,
  output wire input0_ready,
  input [W-1:0] input1_data,
  input input1_valid,
  output wire input1_ready,
  output reg [W-1:0] output_data,
  output reg output_valid,
  input output_ready
);

  reg [W-1:0] buf0, buf1;
  reg buf0_valid, buf1_valid;
  wire both_valid = buf0_valid && buf1_valid;
  wire output_transfer = both_valid && output_ready;

  assign input0_ready = !buf0_valid || (output_transfer && buf1_valid);
  assign input1_ready = !buf1_valid || (output_transfer && buf0_valid);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      buf0_valid <= 0;
      buf1_valid <= 0;
      output_valid <= 0;
      output_data <= 0;
    end else begin
      if (output_transfer) begin
        output_valid <= 1;
        output_data <= buf0 + buf1;
        buf0_valid <= 0;
        buf1_valid <= 0;
      end else begin
        output_valid <= 0;
      end

      if (input0_valid && input0_ready) begin
        buf0 <= input0_data;
        buf0_valid <= 1;
      end
      if (input1_valid && input1_ready) begin
        buf1 <= input1_data;
        buf1_valid <= 1;
      end
    end
  end
endmodule
