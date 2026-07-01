module top (
    input wire clk,
    input wire rst_n,
    input wire we,
    input wire [1:0] addr,
    input wire [15:0] wdata,
    output reg [15:0] rdata
);

  reg [15:0] mem [0:3];
  integer i;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rdata <= 16'd0;
      for (i = 0; i < 4; i = i + 1) begin
        mem[i] <= 16'd0;
      end
    end else begin
      if (we) begin
        mem[addr] <= wdata;
      end
      rdata <= mem[addr];
    end
  end

endmodule
