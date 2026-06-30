module stream_join #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    output wire in0_ready,
    input wire [DATA_WIDTH-1:0] in0_data,
    input wire in1_valid,
    output wire in1_ready,
    input wire [DATA_WIDTH-1:0] in1_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
    reg out_valid_reg;
    reg [DATA_WIDTH-1:0] out_data_reg;
    wire can_output = in0_valid && in1_valid && !out_valid_reg;

    assign in0_ready = in1_valid && !out_valid_reg;
    assign in1_ready = in0_valid && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign out_data = out_data_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_reg <= 1'b0;
      end else begin
        if (can_output) begin
          out_valid_reg <= 1'b1;
          out_data_reg <= in0_data + in1_data;
        end else if (out_valid_reg && out_ready) begin
          out_valid_reg <= 1'b0;
        end
      end
    end
endmodule
