module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [DATA_WIDTH-1:0] out_data,
    output wire out_valid,
    input wire out_ready
);
      reg [DATA_WIDTH-1:0] data_reg;
      reg valid_reg;

      assign in_ready = !valid_reg || out_ready;
      assign out_valid = valid_reg;
      assign out_data = data_reg;

      always @(posedge clk or negedge rst_n) begin
          if (!rst_n) begin
              valid_reg <= 1'b0;
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
