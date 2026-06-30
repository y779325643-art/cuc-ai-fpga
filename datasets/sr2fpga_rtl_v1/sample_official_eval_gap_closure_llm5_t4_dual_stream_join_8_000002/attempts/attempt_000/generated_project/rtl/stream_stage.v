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
    // Simple pipeline register stage
    reg [DATA_WIDTH-1:0] data_r;
    reg valid_r;

    assign out_data = data_r;
    assign out_valid = valid_r;
    assign in_ready = !valid_r || out_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        data_r <= 0;
        valid_r <= 0;
      end else begin
        if (in_valid && in_ready) begin
          data_r <= in_data;
          valid_r <= 1'b1;
        end else if (valid_r && out_ready) begin
          valid_r <= 1'b0;
        end
      end
    end
endmodule
