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
  reg                 valid_reg;
  reg [DATA_WIDTH-1:0] data_skid;
  reg                 valid_skid;

  always @(posedge clk) begin
      if (!rst_n) begin
          valid_reg <= 1'b0;
          valid_skid <= 1'b0;
      end else begin
          // Output pipeline
          if (out_ready || !valid_reg) begin
              if (valid_skid) begin
                  data_reg <= data_skid;
                  valid_reg <= 1'b1;
                  valid_skid <= 1'b0;
              end else if (in_valid && in_ready) begin
                  data_reg <= in_data;
                  valid_reg <= 1'b1;
              end else begin
                  valid_reg <= 1'b0;
              end
          end
          // Fill skid buffer when output is stalled
          if (valid_reg && in_valid && in_ready && !out_ready) begin
              data_skid <= in_data;
              valid_skid <= 1'b1;
          end
      end
  end

  assign in_ready = !valid_skid;
  assign out_valid = valid_reg;
  assign out_data  = data_reg;
endmodule
