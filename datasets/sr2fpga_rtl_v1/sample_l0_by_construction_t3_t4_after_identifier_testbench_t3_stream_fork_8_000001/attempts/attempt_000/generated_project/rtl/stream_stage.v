module stream_stage #(parameter DATA_WIDTH = 8) (
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
    wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg valid_reg;
    reg [DATA_WIDTH-1:0] data_reg;
    assign out_valid = valid_reg;
    assign out_data = data_reg;
    assign in_ready = !valid_reg || out_ready;
    always @(posedge clk) begin
      if (!rst_n) begin
        valid_reg <= 1'b0;
        data_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        if (in_valid && in_ready) begin
          data_reg <= in_data;
          valid_reg <= 1'b1;
        end else if (out_valid && out_ready) begin
          valid_reg <= 1'b0;
        end
      end
    end
endmodule
