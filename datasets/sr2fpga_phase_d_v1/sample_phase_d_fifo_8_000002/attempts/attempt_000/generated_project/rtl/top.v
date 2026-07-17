module top #(parameter DATA_WIDTH = 8, parameter DEPTH = 4, parameter ADDR_WIDTH = 2) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);

  wire u_fifo__in_valid;
  wire u_fifo__in_ready;
  wire [DATA_WIDTH-1:0] u_fifo__in_data;
  wire u_fifo__out_valid;
  wire u_fifo__out_ready;
  wire [DATA_WIDTH-1:0] u_fifo__out_data;

  assign u_fifo__in_data = in_data;
  assign u_fifo__in_valid = in_valid;
  assign in_ready = u_fifo__in_ready;
  assign out_data = u_fifo__out_data;
  assign out_valid = u_fifo__out_valid;
  assign u_fifo__out_ready = out_ready;

  fifo_core #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH), .ADDR_WIDTH(ADDR_WIDTH)) u_fifo (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(u_fifo__in_valid),
    .in_ready(u_fifo__in_ready),
    .in_data(u_fifo__in_data),
    .out_valid(u_fifo__out_valid),
    .out_ready(u_fifo__out_ready),
    .out_data(u_fifo__out_data)
  );

endmodule
