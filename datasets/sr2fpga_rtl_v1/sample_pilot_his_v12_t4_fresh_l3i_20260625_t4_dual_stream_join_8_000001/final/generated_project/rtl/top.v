module top #(parameter DATA_WIDTH=8) (
    input wire clk,
    input wire rst_n,
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

// Internal wires
wire [DATA_WIDTH-1:0] buf0_m_data, buf1_m_data, join_m_data, acc_m_data, stage_m_data;
wire buf0_m_valid, buf1_m_valid, join_m_valid, acc_m_valid, stage_m_valid;
wire buf0_s_ready, buf1_s_ready, join_s0_ready, join_s1_ready, acc_s_ready, stage_s_ready;

// Input skid buffers
skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in0_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(in0_valid),
    .s_ready(in0_ready),
    .s_data(in0_data),
    .m_valid(buf0_m_valid),
    .m_ready(join_s0_ready),
    .m_data(buf0_m_data)
);

skid_buffer #(.DATA_WIDTH(DATA_WIDTH)) in1_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(in1_valid),
    .s_ready(in1_ready),
    .s_data(in1_data),
    .m_valid(buf1_m_valid),
    .m_ready(join_s1_ready),
    .m_data(buf1_m_data)
);

// Stream join
stream_join #(.DATA_WIDTH(DATA_WIDTH)) join_core (
    .clk(clk),
    .rst_n(rst_n),
    .s0_valid(buf0_m_valid),
    .s0_ready(join_s0_ready),
    .s0_data(buf0_m_data),
    .s1_valid(buf1_m_valid),
    .s1_ready(join_s1_ready),
    .s1_data(buf1_m_data),
    .m_valid(join_m_valid),
    .m_ready(acc_s_ready),
    .m_data(join_m_data)
);

// Accumulator core
accumulator_core #(.DATA_WIDTH(DATA_WIDTH)) accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(join_m_valid),
    .s_ready(acc_s_ready),
    .s_data(join_m_data),
    .m_valid(acc_m_valid),
    .m_ready(stage_s_ready),
    .m_data(acc_m_data)
);

// Output stage
stream_stage #(.DATA_WIDTH(DATA_WIDTH)) out_stage (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(acc_m_valid),
    .s_ready(stage_s_ready),
    .s_data(acc_m_data),
    .m_valid(out_valid),
    .m_ready(out_ready),
    .m_data(out_data)
);

endmodule
