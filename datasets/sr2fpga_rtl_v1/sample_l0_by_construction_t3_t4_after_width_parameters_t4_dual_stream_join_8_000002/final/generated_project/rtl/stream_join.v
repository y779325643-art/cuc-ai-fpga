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
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg out_valid_reg;
    reg [DATA_WIDTH-1:0] out_data_reg;

    wire can_accept = !out_valid_reg || out_ready;
    assign in0_ready = can_accept && in1_valid;
    assign in1_ready = can_accept && in0_valid;
    assign out_valid = out_valid_reg;
    assign out_data = out_data_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_reg <= 1'b0;
        out_data_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        if (in0_valid && in1_valid && in0_ready && in1_ready) begin
          out_valid_reg <= 1'b1;
          out_data_reg <= in0_data + in1_data;
        end else if (out_ready) begin
          out_valid_reg <= 1'b0;
        end
      end
    end
endmodule
