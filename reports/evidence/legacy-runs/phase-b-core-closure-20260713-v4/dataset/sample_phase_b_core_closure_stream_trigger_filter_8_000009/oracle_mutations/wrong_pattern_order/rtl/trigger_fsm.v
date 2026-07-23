module trigger_fsm #(parameter WIDTH = 8) (
    input wire clk, input wire rst_n, input wire match_valid, output wire match_ready,
    input wire [31:0] match_index, input wire [WIDTH*4-1:0] match_word,
    output reg trigger_valid, input wire trigger_ready, output reg [31:0] trigger_index,
    output reg [WIDTH*4-1:0] trigger_word
);
  assign match_ready = !trigger_valid || trigger_ready;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      trigger_valid <= 1'b0;
      trigger_index <= 32'd0;
      trigger_word <= {(WIDTH*4){1'b0}};
    end else if (match_ready) begin
      trigger_valid <= match_valid;
      if (match_valid) begin
        trigger_index <= match_index;
        trigger_word <= match_word;
      end
    end
  end
endmodule
