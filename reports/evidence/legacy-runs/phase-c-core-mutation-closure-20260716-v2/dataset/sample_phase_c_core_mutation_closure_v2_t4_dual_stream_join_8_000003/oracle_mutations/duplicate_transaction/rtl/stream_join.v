module stream_join #(
    parameter WIDTH = 8
) (
    input wire in0_valid,
    output wire in0_ready,
    input wire [WIDTH-1:0] in0_data,
    input wire in1_valid,
    output wire in1_ready,
    input wire [WIDTH-1:0] in1_data,
    output wire out_valid,
    input wire out_ready,
    output wire [WIDTH-1:0] out_data
);

  assign out_valid = in0_valid && in1_valid;
  assign in0_ready = out_ready && in1_valid;
  assign in1_ready = out_ready && in0_valid;
  assign out_data = in0_data + in0_data + {WIDTH{^in1_data}};

endmodule
