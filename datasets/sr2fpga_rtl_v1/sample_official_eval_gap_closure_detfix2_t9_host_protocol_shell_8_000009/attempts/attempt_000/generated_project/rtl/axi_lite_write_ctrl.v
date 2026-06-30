module axi_lite_write_ctrl #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire awvalid,
    output wire awready,
    input wire [3:0] awaddr,
    input wire wvalid,
    output wire wready,
    input wire [DATA_WIDTH-1:0] wdata,
    input wire wstrb,
    output reg bvalid,
    input wire bready,
    output wire write_valid,
    output wire [3:0] write_addr,
    output wire [DATA_WIDTH-1:0] write_data
);

  wire accept_write;

  assign awready = !bvalid;
  assign wready = !bvalid;
  assign accept_write = awvalid && wvalid && awready && wready && wstrb;
  assign write_valid = accept_write;
  assign write_addr = awaddr;
  assign write_data = wdata;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      bvalid <= 1'b0;
    end else begin
      if (accept_write) begin
        bvalid <= 1'b1;
      end else if (bvalid && bready) begin
        bvalid <= 1'b0;
      end
    end
  end

endmodule
