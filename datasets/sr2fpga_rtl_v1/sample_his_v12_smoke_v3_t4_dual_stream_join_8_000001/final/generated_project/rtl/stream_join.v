module stream_join #(parameter WIDTH=8) (
    input clk, rst_n,
    input [WIDTH-1:0] s0_tdata,
    input s0_tvalid,
    output s0_tready,
    input [WIDTH-1:0] s1_tdata,
    input s1_tvalid,
    output s1_tready,
    output [WIDTH-1:0] m_tdata,
    output m_tvalid,
    input m_tready
);
wire both_valid = s0_tvalid && s1_tvalid;
assign s0_tready = m_tready && both_valid;
assign s1_tready = m_tready && both_valid;
assign m_tvalid = both_valid;
assign m_tdata = s0_tdata + s1_tdata;
endmodule
