module axi_lite_read_ctrl (
    input wire clk,
    input wire rst_n,
    input wire arvalid,
    output wire arready,
    input wire [3:0] araddr,
    output reg rvalid,
    input wire rready,
    output wire read_valid,
    output wire [3:0] read_addr
);

  wire accept_read;

  assign arready = !rvalid;
  assign accept_read = arvalid && arready;
  assign read_valid = accept_read;
  assign read_addr = araddr;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rvalid <= 1'b0;
    end else begin
      if (accept_read) begin
        rvalid <= 1'b1;
      end else if (rvalid && rready) begin
        rvalid <= 1'b0;
      end
    end
  end

endmodule
