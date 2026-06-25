module accumulator_core #(parameter W = 8) (
  input clk, reset_n,
  input valid_in,
  input [W-1:0] data_in,
  output ready_out,
  output valid_out,
  output [W-1:0] data_out,
  input ready_in
);

reg [W-1:0] acc_reg;
reg acc_valid;

assign ready_out = !acc_valid || (acc_valid && ready_in);
assign valid_out = acc_valid;
assign data_out = acc_reg;

always @(posedge clk or negedge reset_n) begin
  if (!reset_n) begin
    acc_reg <= 0;
    acc_valid <= 0;
  end else begin
    if (valid_in && ready_out) begin
      acc_reg <= acc_reg + data_in;
      acc_valid <= 1;
    end else if (ready_in && acc_valid) begin
      acc_valid <= 0;
    end
  end
end

endmodule
