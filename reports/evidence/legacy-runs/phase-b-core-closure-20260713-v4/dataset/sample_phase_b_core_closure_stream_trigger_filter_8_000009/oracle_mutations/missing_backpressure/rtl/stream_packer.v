module stream_packer #(parameter WIDTH = 8) (
    input wire clk, input wire rst_n, input wire event_valid, output wire event_ready,
    input wire [31:0] event_index, input wire [WIDTH*4-1:0] event_word,
    output reg out_valid, input wire out_ready, output reg [31:0] out_match_index,
    output reg [WIDTH*4-1:0] out_match_word
);
  assign event_ready = !out_valid || out_ready || out_valid;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      out_match_index <= 32'd0;
      out_match_word <= {(WIDTH*4){1'b0}};
    end else if (event_ready) begin
      out_valid <= event_valid;
      if (event_valid) begin
        out_match_index <= event_index;
        out_match_word <= event_word;
      end
    end
  end
endmodule
