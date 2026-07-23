module pattern_matcher #(
    parameter WIDTH = 8,
    parameter [WIDTH-1:0] TOKEN0 = 8'h11,
    parameter [WIDTH-1:0] TOKEN1 = 8'h22,
    parameter [WIDTH-1:0] TOKEN2 = 8'h33,
    parameter [WIDTH-1:0] TOKEN3 = 8'h11
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output reg match_valid,
    input wire match_ready,
    output reg [31:0] match_index,
    output reg [WIDTH*4-1:0] match_word
);

  reg [WIDTH-1:0] token0;
  reg [WIDTH-1:0] token1;
  reg [WIDTH-1:0] token2;
  reg [1:0] window_count;
  reg [31:0] accepted_index;

  assign in_ready = !match_valid || match_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      token0 <= {WIDTH{1'b0}};
      token1 <= {WIDTH{1'b0}};
      token2 <= {WIDTH{1'b0}};
      window_count <= 2'd0;
      accepted_index <= 32'd0;
      match_valid <= 1'b0;
      match_index <= 32'd0;
      match_word <= {(WIDTH*4){1'b0}};
    end else if (in_ready) begin
      match_valid <= 1'b0;
      if (in_valid) begin
        if (window_count == 2'd3 && token0 == TOKEN0 && token1 == TOKEN1 && token2 == TOKEN2 && in_data == TOKEN3) begin
          match_valid <= 1'b1;
          match_index <= accepted_index;
          match_word <= {token0, token1, token2, in_data};
        end
        token0 <= {WIDTH{1'b0}};
        token1 <= token2;
        token2 <= in_data;
        if (window_count != 2'd3) begin
          window_count <= window_count + 2'd1;
        end
        accepted_index <= accepted_index + 32'd1;
      end
    end
  end
endmodule
