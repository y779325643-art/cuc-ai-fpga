module stream_fork #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [DATA_WIDTH-1:0] out0_data,
    output wire out0_valid,
    input wire out0_ready,
    output wire [DATA_WIDTH-1:0] out1_data,
    output wire out1_valid,
    input wire out1_ready
);
      assign in_ready = out0_ready && out1_ready;
      assign out0_valid = in_valid && in_ready;
      assign out1_valid = in_valid && in_ready;
      assign out0_data = in_data;
      assign out1_data = in_data;
endmodule
