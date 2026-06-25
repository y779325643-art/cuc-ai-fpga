module top #(parameter WIDTH=8) (
    input clk, rst_n,
    input [WIDTH-1:0] s_axis0_tdata,
    input s_axis0_tvalid,
    output s_axis0_tready,
    input [WIDTH-1:0] s_axis1_tdata,
    input s_axis1_tvalid,
    output s_axis1_tready,
    output [WIDTH-1:0] m_axis_tdata,
    output m_axis_tvalid,
    input m_axis_tready
);
wire [WIDTH-1:0] in0_to_join, in1_to_join;
wire in0_to_join_valid, in1_to_join_valid;
wire in0_to_join_ready, in1_to_join_ready;
wire [WIDTH-1:0] join_to_acc;
wire join_to_acc_valid, join_to_acc_ready;
wire [WIDTH-1:0] acc_to_out;
wire acc_to_out_valid, acc_to_out_ready;

skid_buffer #(.WIDTH(WIDTH)) in0_buffer (
    .clk(clk), .rst_n(rst_n),
    .s_tdata(s_axis0_tdata), .s_tvalid(s_axis0_tvalid), .s_tready(s_axis0_tready),
    .m_tdata(in0_to_join), .m_tvalid(in0_to_join_valid), .m_tready(in0_to_join_ready)
);
skid_buffer #(.WIDTH(WIDTH)) in1_buffer (
    .clk(clk), .rst_n(rst_n),
    .s_tdata(s_axis1_tdata), .s_tvalid(s_axis1_tvalid), .s_tready(s_axis1_tready),
    .m_tdata(in1_to_join), .m_tvalid(in1_to_join_valid), .m_tready(in1_to_join_ready)
);
stream_join #(.WIDTH(WIDTH)) join_core (
    .clk(clk), .rst_n(rst_n),
    .s0_tdata(in0_to_join), .s0_tvalid(in0_to_join_valid), .s0_tready(in0_to_join_ready),
    .s1_tdata(in1_to_join), .s1_tvalid(in1_to_join_valid), .s1_tready(in1_to_join_ready),
    .m_tdata(join_to_acc), .m_tvalid(join_to_acc_valid), .m_tready(join_to_acc_ready)
);
accumulator_core #(.WIDTH(WIDTH)) accumulator (
    .clk(clk), .rst_n(rst_n),
    .s_tdata(join_to_acc), .s_tvalid(join_to_acc_valid), .s_tready(join_to_acc_ready),
    .m_tdata(acc_to_out), .m_tvalid(acc_to_out_valid), .m_tready(acc_to_out_ready)
);
stream_stage #(.WIDTH(WIDTH)) out_stage (
    .clk(clk), .rst_n(rst_n),
    .s_tdata(acc_to_out), .s_tvalid(acc_to_out_valid), .s_tready(acc_to_out_ready),
    .m_tdata(m_axis_tdata), .m_tvalid(m_axis_tvalid), .m_tready(m_axis_tready)
);
endmodule
