module stream_stage #(parameter DATA_WIDTH = 8) (
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
    reg out_valid_reg;
    reg [DATA_WIDTH-1:0] out_data_reg;

    assign in_ready = !out_valid_reg || out_ready;
    assign out_valid = out_valid_reg;
    assign out_data = out_data_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_reg <= 1'b0;
        out_data_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        if (in_valid && in_ready) begin
          out_valid_reg <= 1'b1;
          out_data_reg <= in_data;
        end else if (out_ready) begin
          out_valid_reg <= 1'b0;
        end
      end
    end
endmodule
