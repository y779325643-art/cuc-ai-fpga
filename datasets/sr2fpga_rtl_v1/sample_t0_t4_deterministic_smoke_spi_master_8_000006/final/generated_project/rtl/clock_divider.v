module clock_divider (
    input wire clk,
    input wire rst_n,
    input wire enable,
    output wire tick
);

  reg div_count;

  assign tick = enable && div_count;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      div_count <= 1'b0;
    end else if (enable) begin
      div_count <= ~div_count;
    end else begin
      div_count <= 1'b0;
    end
  end

endmodule
