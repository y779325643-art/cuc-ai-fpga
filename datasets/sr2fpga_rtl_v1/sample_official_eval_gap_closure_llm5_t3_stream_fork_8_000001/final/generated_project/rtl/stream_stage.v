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
    reg out_valid_r;
    reg [DATA_WIDTH-1:0] out_data_r;

    assign out_valid = out_valid_r;
    assign out_data = out_data_r;
    assign in_ready = !out_valid_r || out_ready;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_r <= 1'b0;
        out_data_r <= {DATA_WIDTH{1'b0}};
      end else begin
        if (in_valid && in_ready) begin
          out_data_r <= in_data;
          out_valid_r <= 1'b1;
        end else if (out_valid_r && out_ready) begin
          out_valid_r <= 1'b0;
        end
      end
    end
endmodule
