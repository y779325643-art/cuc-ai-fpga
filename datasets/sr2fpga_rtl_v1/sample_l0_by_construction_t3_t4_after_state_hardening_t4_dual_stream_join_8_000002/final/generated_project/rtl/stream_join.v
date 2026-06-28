module stream_join #(parameter DATA_WIDTH = 8) (
    input wire in0_valid,
    input wire [DATA_WIDTH-1:0] in0_data,
    output wire in0_ready,
    input wire in1_valid,
    input wire [DATA_WIDTH-1:0] in1_data,
    output wire in1_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
  module stream_join #(parameter DATA_WIDTH = 8) (
      input wire in0_valid,
      input wire [DATA_WIDTH-1:0] in0_data,
      output wire in0_ready,
      input wire in1_valid,
      input wire [DATA_WIDTH-1:0] in1_data,
      output wire in1_ready,
      output wire out_valid,
      output wire [DATA_WIDTH-1:0] out_data,
      input wire out_ready
  );
    assign out_valid = in0_valid && in1_valid;
    assign out_data  = in0_data;
    assign in0_ready = in1_valid && out_ready;
    assign in1_ready = in0_valid && out_ready;
  endmodule
endmodule
