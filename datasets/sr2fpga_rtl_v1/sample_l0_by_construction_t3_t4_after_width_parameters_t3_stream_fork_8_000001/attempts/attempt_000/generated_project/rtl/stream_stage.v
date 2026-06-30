module stream_stage #(parameter DATA_WIDTH = 0) (
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
    reg [DATA_WIDTH-1:0] stage_data;
    reg stage_valid;

    assign out_valid = stage_valid;
    assign out_data  = stage_data;
    assign in_ready  = !stage_valid | out_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        stage_valid <= 1'b0;
        stage_data  <= '0;
      end else begin
        if (in_valid & in_ready) begin
          stage_valid <= 1'b1;
          stage_data  <= in_data;
        end else if (out_valid & out_ready) begin
          stage_valid <= 1'b0;
        end
      end
    end
endmodule
