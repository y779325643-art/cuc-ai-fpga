module top #(parameter WIDTH=8)(
    input clk,
    input rst_n,
    input in_valid,
    input [WIDTH-1:0] in_data,
    output out0_valid,
    output [WIDTH-1:0] out0_data,
    output out1_valid,
    output [WIDTH-1:0] out1_data,
    input out0_ready,
    input out1_ready
);

wire [WIDTH-1:0] skid_data;
wire skid_valid, skid_ready;

wire [WIDTH-1:0] fork_data0, fork_data1;
wire fork_valid0, fork_valid1, fork_ready0, fork_ready1;

wire [WIDTH-1:0] stage_data0, stage_data1;
wire stage_valid0, stage_valid1, stage_ready0, stage_ready1;

// Instantiations
skid_buffer #(.WIDTH(WIDTH)) skid (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .out_valid(skid_valid),
    .out_data(skid_data),
    .in_ready(skid_ready),
    .out_ready(fork_ready0 & fork_ready1)  // fork ready when both downstream ready? Actually fork in_ready is output; we need fork to indicate it can accept. So we connect skid.out_ready to fork's in_ready? No, skid.out_ready is input to skid, meaning downstream ready. So we need to connect to fork's in_ready? Wait, correct: skid.out_ready <- fork.in_ready. fork.in_ready is output from fork. So we need a wire.
);

stream_fork #(.WIDTH(WIDTH)) fork (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(skid_valid),
    .in_data(skid_data),
    .out0_valid(fork_valid0),
    .out0_data(fork_data0),
    .out1_valid(fork_valid1),
    .out1_data(fork_data1),
    .in_ready(fork_in_ready),
    .out0_ready(stage_ready0),
    .out1_ready(stage_ready1)
);

assign skid.out_ready = fork_in_ready;

stream_stage #(.WIDTH(WIDTH)) stage0 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(fork_valid0),
    .in_data(fork_data0),
    .out_valid(out0_valid),
    .out_data(out0_data),
    .in_ready(stage_ready0),
    .out_ready(out0_ready)
);

stream_stage #(.WIDTH(WIDTH)) stage1 (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(fork_valid1),
    .in_data(fork_data1),
    .out_valid(out1_valid),
    .out_data(out1_data),
    .in_ready(stage_ready1),
    .out_ready(out1_ready)
);

endmodule
