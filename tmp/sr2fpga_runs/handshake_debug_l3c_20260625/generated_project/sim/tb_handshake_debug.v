`timescale 1ns/1ps

module tb_handshake_debug;
    reg clk;
    reg reset_n;
    reg [7:0] in0_data;
    reg in0_valid;
    wire in0_ready;
    reg [7:0] in1_data;
    reg in1_valid;
    wire in1_ready;
    wire [7:0] out_data;
    wire out_valid;
    reg out_ready;

    top dut (
        .clk(clk),
        .reset_n(reset_n),
        .in0_data(in0_data),
        .in0_valid(in0_valid),
        .in0_ready(in0_ready),
        .in1_data(in1_data),
        .in1_valid(in1_valid),
        .in1_ready(in1_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    integer cycle;

    always @(negedge clk) begin
        cycle = cycle + 1;
        $display(
            "C%0d ext i0_vr=%0b%0b i1_vr=%0b%0b out_vr=%0b%0b out=%0d | b0_vr=%0b%0b b1_vr=%0b%0b join_vr=%0b%0b jd=%0d acc_vr=%0b%0b ad=%0d stage_sv=%0b stage_ov=%0b",
            cycle,
            in0_valid, in0_ready,
            in1_valid, in1_ready,
            out_valid, out_ready,
            out_data,
            dut.in0_buffer_valid_out, dut.in0_buffer_ready_out,
            dut.in1_buffer_valid_out, dut.in1_buffer_ready_out,
            dut.join_core_out_valid, dut.join_core_out_ready,
            dut.join_core_out_data,
            dut.accumulator_out_valid, dut.accumulator_out_ready,
            dut.accumulator_out_data,
            dut.out_stage.stage_valid,
            dut.out_stage.out_valid
        );
    end

    initial begin
        cycle = 0;
        reset_n = 0;
        in0_data = 0;
        in1_data = 0;
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 1;

        #20 reset_n = 1;
        #10;

        in0_data = 8'd1;
        in1_data = 8'd10;
        in0_valid = 1;
        in1_valid = 1;
        @(posedge clk);
        in0_valid = 0;
        in1_valid = 0;

        repeat (20) @(posedge clk);
        $finish;
    end
endmodule
