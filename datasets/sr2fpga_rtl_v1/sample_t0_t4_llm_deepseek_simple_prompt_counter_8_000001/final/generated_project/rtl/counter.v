module counter #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire en,
    output wire [WIDTH-1:0] count
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  reg [WIDTH-1:0] cnt;
  assign count = cnt;

  always @(posedge clk) begin
    if (!rst_n) begin
      cnt <= {WIDTH{1'b0}};
    end else if (en) begin
      cnt <= cnt + 1'b1;
    end
  end
endmodule
