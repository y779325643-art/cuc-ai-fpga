module skid_buffer #(parameter W = 8) (
  input clk, reset_n,
  input valid_in,
  input [W-1:0] data_in,
  output ready_out,
  output valid_out,
  output [W-1:0] data_out,
  input ready_in
);

reg [W-1:0] data_store;
reg store_valid;

assign ready_out = !store_valid || (store_valid && ready_in);
assign valid_out = store_valid;
assign data_out = data_store;

always @(posedge clk or negedge reset_n) begin
  if (!reset_n) begin
    store_valid <= 0;
    data_store <= 0;
  end else begin
    if (valid_in && ready_out) begin
      data_store <= data_in;
      store_valid <= 1;
    end else if (ready_in && store_valid) begin
      store_valid <= 0;
    end
  end
end

endmodule
