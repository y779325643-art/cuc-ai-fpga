module top #(
    parameter WIDTH = 8,
    parameter [WIDTH-1:0] TOKEN0 = 8'h11,
    parameter [WIDTH-1:0] TOKEN1 = 8'h22,
    parameter [WIDTH-1:0] TOKEN2 = 8'h33,
    parameter [WIDTH-1:0] TOKEN3 = 8'h11
) (
    input wire clk, input wire rst_n, input wire in_valid, output wire in_ready,
    input wire [7:0] in_data, output wire out_valid, input wire out_ready,
    output wire [31:0] out_match_index, output wire [31:0] out_match_word
);
  pattern_matcher #(.WIDTH(WIDTH), .TOKEN0(TOKEN0), .TOKEN1(TOKEN1), .TOKEN2(TOKEN2), .TOKEN3(TOKEN3)) u_pattern_matcher (
    .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data),
    .match_valid(out_valid), .match_ready(out_ready), .match_index(out_match_index), .match_word(out_match_word)
  );
endmodule
