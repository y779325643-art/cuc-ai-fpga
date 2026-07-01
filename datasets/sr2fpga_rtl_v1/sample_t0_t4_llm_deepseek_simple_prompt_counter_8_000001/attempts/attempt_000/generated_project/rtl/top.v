module top #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire en,
    output wire [7:0] count
);

  wire cnt_inst__en;
  wire [WIDTH-1:0] cnt_inst__count;

  assign cnt_inst__en = en;
  assign count = cnt_inst__count;

  counter #(.WIDTH(WIDTH)) cnt_inst (
    .clk(clk),
    .rst_n(rst_n),
    .en(cnt_inst__en),
    .count(cnt_inst__count)
  );

endmodule
