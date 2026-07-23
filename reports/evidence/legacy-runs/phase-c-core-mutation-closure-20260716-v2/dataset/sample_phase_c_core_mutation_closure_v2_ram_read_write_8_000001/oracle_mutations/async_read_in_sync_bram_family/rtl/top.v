module top (
    input wire clk,
    input wire rst_n,
    input wire we,
    input wire [1:0] addr,
    input wire [7:0] wdata,
    output wire [7:0] rdata
);

  reg [7:0] mem [0:3];
  integer i;

  assign rdata = mem[addr];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i = 0; i < 4; i = i + 1) begin
        mem[i] <= 8'd0;
      end
    end else begin
      if (we) begin
        mem[addr] <= wdata;
      end
    end
  end

endmodule
