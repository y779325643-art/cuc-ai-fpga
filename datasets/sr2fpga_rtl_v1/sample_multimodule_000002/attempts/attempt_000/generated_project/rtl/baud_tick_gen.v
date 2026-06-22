module baud_tick_gen (
    input wire clk,
    input wire rst_n,
    input wire enable,
    output wire tick
);

  reg [1:0] div_count;

  assign tick = enable && (div_count == 2'd3);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      div_count <= 2'd0;
    end else if (enable) begin
      div_count <= div_count + 2'd1;
    end else begin
      div_count <= 2'd0;
    end
  end

endmodule
