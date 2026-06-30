module skid_buffer (
  input clk,
  input rst_n,
  input [7:0] in_data,
  input in_valid,
  output in_ready,
  output [7:0] out_data,
  output out_valid,
  input out_ready
);

  reg [7:0] skid_data;
  reg skid_full;

  assign in_ready = !skid_full;
  assign out_valid = (in_valid && !skid_full) || skid_full;
  assign out_data  = skid_full ? skid_data : in_data;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      skid_full <= 1'b0;
      skid_data <= 8'd0;
    end else begin
      if (in_valid && !skid_full) begin
        if (!out_ready) begin
          skid_data <= in_data;
          skid_full <= 1'b1;
        end
      end else if (skid_full && out_ready) begin
        skid_full <= 1'b0;
      end
    end
  end

endmodule
