module top #(parameter DATA_WIDTH = 8, parameter DEPTH = 16, parameter ADDR_WIDTH = 4) (
    input wire clk,
    input wire rst_n,
    input wire wr_valid,
    output wire wr_ready,
    input wire [DATA_WIDTH-1:0] wr_data,
    output wire rd_valid,
    input wire rd_ready,
    output wire [DATA_WIDTH-1:0] rd_data
);

  wire u_fifo__wr_valid;
  wire u_fifo__wr_ready;
  wire [DATA_WIDTH-1:0] u_fifo__wr_data;
  wire u_fifo__rd_valid;
  wire u_fifo__rd_ready;
  wire [DATA_WIDTH-1:0] u_fifo__rd_data;

  assign u_fifo__wr_data = wr_data;
  assign u_fifo__wr_valid = wr_valid;
  assign wr_ready = u_fifo__wr_ready;
  assign rd_data = u_fifo__rd_data;
  assign rd_valid = u_fifo__rd_valid;
  assign u_fifo__rd_ready = rd_ready;

  sync_fifo #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH), .ADDR_WIDTH(ADDR_WIDTH)) u_fifo (
    .clk(clk),
    .rst_n(rst_n),
    .wr_valid(u_fifo__wr_valid),
    .wr_ready(u_fifo__wr_ready),
    .wr_data(u_fifo__wr_data),
    .rd_valid(u_fifo__rd_valid),
    .rd_ready(u_fifo__rd_ready),
    .rd_data(u_fifo__rd_data)
  );

endmodule
