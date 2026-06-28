module skid_buffer (
  input wire clk,
  input wire reset_n,
  input wire in_valid,
  input wire [7:0] in_data,
  output wire in_ready,
  output wire out_valid,
  output wire [7:0] out_data,
  input wire out_ready
);
  reg main_valid, skid_valid;
  reg [7:0] main_data, skid_data;

  assign in_ready = !skid_valid && (!main_valid || out_ready);
  assign out_valid = main_valid | skid_valid;
  assign out_data = main_valid ? main_data : skid_data;

  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      main_valid <= 0;
      skid_valid <= 0;
      main_data <= 0;
      skid_data <= 0;
    end else begin
      if (out_ready) begin
        if (skid_valid) begin
          main_data <= skid_data;
          main_valid <= 1;
          skid_valid <= 0;
        end else begin
          main_valid <= 0;
        end
      end

      if (in_valid && in_ready) begin
        if (!main_valid || (out_ready && !skid_valid)) begin
          main_data <= in_data;
          main_valid <= 1;
        end else begin
          skid_data <= in_data;
          skid_valid <= 1;
        end
      end
    end
  end
endmodule
