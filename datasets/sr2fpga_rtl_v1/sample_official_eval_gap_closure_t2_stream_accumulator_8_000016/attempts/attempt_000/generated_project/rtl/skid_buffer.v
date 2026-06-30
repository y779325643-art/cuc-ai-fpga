module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  reg [DATA_WIDTH-1:0] data_reg;
  reg valid_reg;
  reg [DATA_WIDTH-1:0] skid_data;
  reg skid_valid;

  assign out_data = skid_valid ? skid_data : data_reg;
  assign out_valid = valid_reg || skid_valid;
  assign in_ready = !skid_valid;

  always @(posedge clk) begin
    if (!rst_n) begin
      valid_reg <= 1'b0;
      skid_valid <= 1'b0;
    end else begin
      if (in_valid && in_ready) begin
        if (!valid_reg) begin
          data_reg <= in_data;
          valid_reg <= 1'b1;
        end else if (!skid_valid) begin
          skid_data <= in_data;
          skid_valid <= 1'b1;
        end
      end
      if (out_ready) begin
        if (valid_reg) begin
          if (skid_valid) begin
            data_reg <= skid_data;
            skid_valid <= 1'b0;
          end else begin
            valid_reg <= 1'b0;
          end
        end else if (skid_valid) begin
          data_reg <= skid_data;
          skid_valid <= 1'b0;
          valid_reg <= 1'b1;
        end
      end
    end
  end
endmodule
