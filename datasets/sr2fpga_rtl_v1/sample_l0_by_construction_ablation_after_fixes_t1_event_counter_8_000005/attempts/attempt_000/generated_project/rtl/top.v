module top (
    input wire [1-1:0] clk,
    input wire [1-1:0] rst_n,
    input wire [1-1:0] event_valid,
    output wire [8-1:0] count
);

  wire [1-1:0] event_gate__event_valid;
  wire [1-1:0] event_gate__count_en;
  wire [1-1:0] counter__en;
  wire [WIDTH-1:0] counter__count;

  event_gate event_gate (
    .clk(clk),
    .rst_n(rst_n),
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
