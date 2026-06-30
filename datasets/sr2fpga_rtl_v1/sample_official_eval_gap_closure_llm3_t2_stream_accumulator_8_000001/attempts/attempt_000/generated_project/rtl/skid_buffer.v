module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    input wire out_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg valid_reg;
    reg [DATA_WIDTH-1:0] data_reg;

    assign out_valid = valid_reg;
    assign out_data = data_reg;
    assign in_ready = !valid_reg || out_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        valid_reg <= 1'b0;
        data_reg <= 0;
      end else begin
        if (in_ready && in_valid) begin
          data_reg <= in_data;
          valid_reg <= 1'b1;
        end else if (out_ready && out_valid) begin
          valid_reg <= 1'b0;
        end
      end
    end
endmodule
