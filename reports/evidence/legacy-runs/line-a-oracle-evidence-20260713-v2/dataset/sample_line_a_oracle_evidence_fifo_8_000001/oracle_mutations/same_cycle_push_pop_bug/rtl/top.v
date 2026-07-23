module top (
    input wire clk,
    input wire rst_n,
    input wire wr_en,
    input wire rd_en,
    input wire [7:0] din,
    output reg [7:0] dout,
    output wire full,
    output wire empty
);

  reg [7:0] mem [0:3];
  reg [1:0] wr_ptr;
  reg [1:0] rd_ptr;
  reg [2:0] count;

  assign full = (count == 3'd4);
  assign empty = (count == 3'd0);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wr_ptr <= 2'd0;
      rd_ptr <= 2'd0;
      count <= 3'd0;
      dout <= 8'd0;
    end else begin
      if (wr_en && !full) begin
        mem[wr_ptr] <= din;
        wr_ptr <= wr_ptr + 2'd1;
      end
      if (rd_en && !empty) begin
        dout <= mem[rd_ptr];
        rd_ptr <= rd_ptr + 2'd1;
      end
      case ({wr_en && !full, rd_en && !empty})
        2'b10: count <= count + 3'd1;
        2'b01: count <= count - 3'd1;
        default: count <= count + 3'd1;
      endcase
    end
  end

endmodule
