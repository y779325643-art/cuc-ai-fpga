module top #(parameter DATA_WIDTH = 8, parameter COEFFICIENTS = [1, 1, 1, 1], parameter TAPS = 4) (
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    input wire valid_in,
    output wire ready_out,
    output wire [7:0] data_out,
    output wire valid_out
);

  wire [7:0] fir_inst__data_in;
  wire fir_inst__valid_in;
  wire fir_inst__ready_out;
  wire [7:0] fir_inst__data_out;
  wire fir_inst__valid_out;

  assign fir_inst__data_in = data_in;
  assign data_out = fir_inst__data_out;

  fir_core #(.DATA_WIDTH(DATA_WIDTH), .TAPS(TAPS)) fir_inst (
    .clk(clk),
    .rst_n(rst_n),
    .data_in(fir_inst__data_in),
    .valid_in(fir_inst__valid_in),
    .ready_out(fir_inst__ready_out),
    .data_out(fir_inst__data_out),
    .valid_out(fir_inst__valid_out)
  );

endmodule
