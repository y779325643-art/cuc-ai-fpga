module stream_join #(parameter DATA_WIDTH = 8) (
    input wire in0_valid,
    output wire in0_ready,
    input wire [DATA_WIDTH-1:0] in0_data,
    input wire in1_valid,
    output wire in1_ready,
    input wire [DATA_WIDTH-1:0] in1_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
  // SR2FPGA_BEHAVIOR_BEGIN
    wire paired_valid;
    wire paired_accept;
    wire [DATA_WIDTH:0] joined_sum_ext;

    assign paired_valid = in0_valid & in1_valid;
    assign paired_accept = paired_valid & out_ready;
    assign joined_sum_ext = {1'b0, in0_data} + {1'b0, in1_data};
    wire _unused_joined_carry = joined_sum_ext[DATA_WIDTH];

    assign out_valid = paired_valid;
    assign out_data = joined_sum_ext[DATA_WIDTH-1:0];
    assign in0_ready = in1_valid & out_ready;
    assign in1_ready = in0_valid & out_ready;
    wire _unused_paired_accept = paired_accept;
  // SR2FPGA_BEHAVIOR_END
endmodule
