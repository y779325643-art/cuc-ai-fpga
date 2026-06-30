module top #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire event_valid,
    output wire [WIDTH-1:0] count
);

  wire event_gate__event_valid;
  wire event_gate__count_en;
  wire counter__en;
  wire [WIDTH-1:0] counter__count;

  event_gate event_gate (
    .event_valid(event_gate__event_valid),
    .count_en(event_gate__count_en)
  );

  counter_core #(.WIDTH(8)) counter (
    .clk(clk),
    .rst_n(rst_n),
    .en(counter__en),
    .count(counter__count)
  );

endmodule
