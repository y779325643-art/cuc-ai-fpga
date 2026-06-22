module top (
    input wire clk,
    input wire reset_n,
    input wire we,
    input wire [1:0] addr,
    input wire [31:0] wdata,
    output reg [31:0] rdata
);

  reg [31:0] mem [0:3];
  integer i;

  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      rdata <= 32'd0;
      for (i = 0; i < 4; i = i + 1) begin
        mem[i] <= 32'd0;
      end
    end else begin
      if (we) begin
        mem[addr] <= wdata;
      end
      rdata <= mem[addr];
    end
  end

endmodule
