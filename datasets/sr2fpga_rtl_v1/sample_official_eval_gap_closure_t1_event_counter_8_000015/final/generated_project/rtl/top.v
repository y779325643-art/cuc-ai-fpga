module top #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire event_valid,
    output wire [DATA_WIDTH-1:0] count
);

  wire event_gate__event_valid;
  wire event_gate__count_en;
  wire counter__en;
  wire [DATA_WIDTH-1:0] counter__count;

  assign event_gate__event_valid = event_valid;
  assign counter__en = event_gate__count_en;
  assign count = counter__count;

  event_gate event_gate (
    .clk(clk),
    .rst_n(rst_n),
    .event_valid(event_gate__event_valid),
    .count_en(event_gate__count_en)
  );

  counter_core #(.DATA_WIDTH(8)) counter (
    .clk(clk),
    .rst_n(rst_n),
    .en(counter__en),
    .count(counter__count)
  );

endmodule
