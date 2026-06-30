module skid_buffer #(parameter WIDTH=8) (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire [WIDTH-1:0] in_data,
  output wire out_valid,
  input wire out_ready,
  output wire [WIDTH-1:0] out_data
);
  reg r_valid;
  reg [WIDTH-1:0] r_data;
  reg skid_valid;
  reg [WIDTH-1:0] skid_data;

  assign out_valid = r_valid;
  assign out_data = r_data;
  assign in_ready = !skid_valid;

  wire output_taken = r_valid && out_ready;
  wire output_will_be_empty = !r_valid || (output_taken && !skid_valid);
  wire input_taken = in_valid && in_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      r_valid <= 1'b0;
      skid_valid <= 1'b0;
      r_data <= 0;
      skid_data <= 0;
    end else begin
      if (output_taken) begin
        if (skid_valid) begin
          r_data <= skid_data;
          r_valid <= 1'b1;
          skid_valid <= 1'b0;
        end else begin
          r_valid <= 1'b0;
        end
      end
      if (input_taken) begin
        if (output_will_be_empty) begin
          r_data <= in_data;
          r_valid <= 1'b1;
        end else begin
          skid_data <= in_data;
          skid_valid <= 1'b1;
        end
      end
    end
  end

endmodule
