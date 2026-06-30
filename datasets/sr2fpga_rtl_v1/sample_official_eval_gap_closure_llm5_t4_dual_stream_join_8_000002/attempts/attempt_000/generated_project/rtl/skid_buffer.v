module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    // Standard skid buffer
    reg [DATA_WIDTH-1:0] data_reg;
    reg valid_reg;

    assign out_data = valid_reg ? data_reg : in_data;
    assign out_valid = valid_reg || in_valid;
    assign in_ready = !valid_reg || out_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        data_reg <= 0;
        valid_reg <= 0;
      end else begin
        if (in_valid && in_ready) begin
          data_reg <= in_data;
          valid_reg <= 1'b1;
        end else if (valid_reg && out_ready) begin
          valid_reg <= 1'b0;
        end
      end
    end
endmodule
