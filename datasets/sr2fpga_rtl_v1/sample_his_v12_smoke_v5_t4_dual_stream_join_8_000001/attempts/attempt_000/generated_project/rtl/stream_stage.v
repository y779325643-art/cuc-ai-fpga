module stream_stage #(parameter W = 8) (
  input clk, reset_n,
  input valid_in,
  input [W-1:0] data_in,
  output ready_out,
  output valid_out,
  output [W-1:0] data_out,
  input ready_in
);

reg [W-1:0] stage_reg;
reg stage_valid;

assign ready_out = !stage_valid || (stage_valid && ready_in);
assign valid_out = stage_valid;
assign data_out = stage_reg;

always @(posedge clk or negedge reset_n) begin
  if (!reset_n) begin
    stage_reg <= 0;
    stage_valid <= 0;
  end else begin
    if (valid_in && ready_out) begin
      stage_reg <= data_in;
      stage_valid <= 1;
    end else if (ready_in && stage_valid) begin
      stage_valid <= 0;
    end
  end
end

endmodule
