module accumulator_core #(parameter W=8) (
  input clk, rst_n,
  input [W-1:0] data_in,
  input valid_in,
  output wire ready_out,
  output reg [W-1:0] data_out,
  output reg valid_out,
  input ready_in
);

  reg [W-1:0] accum;

  assign ready_out = !valid_out || ready_in;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      accum <= 0;
      valid_out <= 0;
      data_out <= 0;
    end else begin
      if (ready_in && valid_out) begin
        valid_out <= 0;
      end
      if (valid_in && ready_out) begin
        accum <= accum + data_in;
        data_out <= accum + data_in;
        valid_out <= 1;
      end
    end
  end
endmodule
