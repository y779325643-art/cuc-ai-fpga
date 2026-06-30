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
    reg [DATA_WIDTH-1:0] data_reg;
    reg valid_reg;

    assign out_data = data_reg;
    assign out_valid = valid_reg;
    assign in_ready = !valid_reg || out_ready;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        valid_reg <= 1'b0;
      end else begin
        if (in_valid && in_ready) begin
          data_reg <= in_data;
          valid_reg <= 1'b1;
        end else if (out_ready && valid_reg) begin
          valid_reg <= 1'b0;
        end
      end
    end
endmodule
