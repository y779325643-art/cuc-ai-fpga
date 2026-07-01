module pwm_timer #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    output reg [WIDTH-1:0] counter
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      counter <= {WIDTH{1'b0}};
    end else begin
      counter <= counter + {{(WIDTH-1){1'b0}}, 1'b1};
    end
  end

endmodule
