module stream_fork #(parameter DATA_WIDTH = 8) (
    input wire [None-1:0] in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire [None-1:0] in_ready,
    output wire [None-1:0] out0_valid,
    output wire [DATA_WIDTH-1:0] out0_data,
    input wire [None-1:0] out0_ready,
    output wire [None-1:0] out1_valid,
    output wire [DATA_WIDTH-1:0] out1_data,
    input wire [None-1:0] out1_ready
);
  module stream_fork #(parameter DATA_WIDTH = 8) (
      input wire [None-1:0] in_valid,
      input wire [DATA_WIDTH-1:0] in_data,
      output wire [None-1:0] in_ready,
      output wire [None-1:0] out0_valid,
      output wire [DATA_WIDTH-1:0] out0_data,
      input wire [None-1:0] out0_ready,
      output wire [None-1:0] out1_valid,
      output wire [DATA_WIDTH-1:0] out1_data,
      input wire [None-1:0] out1_ready
  );
     assign in_ready = out0_ready && out1_ready;
     assign out0_valid = in_valid;
     assign out1_valid = in_valid;
     assign out0_data = in_data;
     assign out1_data = in_data;
  endmodule
endmodule
