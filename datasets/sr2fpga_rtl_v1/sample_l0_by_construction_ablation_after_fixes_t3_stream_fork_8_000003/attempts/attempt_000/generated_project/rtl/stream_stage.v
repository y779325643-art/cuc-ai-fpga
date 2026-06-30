module stream_stage (
  input wire clk,
  input wire reset_n,
  input wire in_valid,
  input wire [7:0] in_data,
  output wire in_ready,
  output reg out_valid,
  output reg [7:0] out_data,
  input wire out_ready
);
  reg valid_reg;
  reg [7:0] data_reg;

  assign in_ready = !valid_reg || out_ready;
  assign out_valid = valid_reg;
  assign out_data = data_reg;

  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      valid_reg <= 0;
      data_reg <= 0;
    end else begin
      if (in_valid && in_ready) begin
        data_reg <= in_data;
        valid_reg <= 1;
      end else if (out_ready) begin
        valid_reg <= 0;
      end
    end
  end
endmodule
