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
  wire match_valid, match_ready;
  wire [31:0] match_index;
  wire [31:0] match_word;
  wire trigger_valid, trigger_ready;
  wire [31:0] trigger_index;
  wire [31:0] trigger_word;

  pattern_matcher #(.WIDTH(WIDTH), .TOKEN0(TOKEN0), .TOKEN1(TOKEN1), .TOKEN2(TOKEN2), .TOKEN3(TOKEN3)) u_pattern_matcher (
    .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data),
    .match_valid(match_valid), .match_ready(match_ready), .match_index(match_index), .match_word(match_word)
  );
  trigger_fsm #(.WIDTH(WIDTH)) u_trigger_fsm (
    .clk(clk), .rst_n(rst_n), .match_valid(match_valid), .match_ready(match_ready), .match_index(match_index), .match_word(match_word),
    .trigger_valid(trigger_valid), .trigger_ready(trigger_ready), .trigger_index(trigger_index), .trigger_word(trigger_word)
  );
  stream_packer #(.WIDTH(WIDTH)) u_stream_packer (
    .clk(clk), .rst_n(rst_n), .event_valid(trigger_valid), .event_ready(trigger_ready), .event_index(trigger_index), .event_word(trigger_word),
    .out_valid(out_valid), .out_ready(out_ready), .out_match_index(out_match_index), .out_match_word(out_match_word)
  );
endmodule
