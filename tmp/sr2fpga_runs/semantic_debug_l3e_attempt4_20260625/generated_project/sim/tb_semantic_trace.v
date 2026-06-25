`timescale 1ns/1ps

module tb_semantic_trace;
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

    reg [7:0] in0_seq [0:4];
    reg [7:0] in1_seq [0:4];
    integer i;
    integer cycle;
    integer observed_sum;

    top dut (
        .clk(clk),
        .reset_n(reset_n),
        .in0_valid(in0_valid),
        .in0_ready(in0_ready),
        .in0_data(in0_data),
        .in1_valid(in1_valid),
        .in1_ready(in1_ready),
        .in1_data(in1_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_data(out_data)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    always @(negedge clk) begin
        if (reset_n) begin
            cycle = cycle + 1;
            $display(
                "C%0d ext in0=%0b%0b:%0d in1=%0b%0b:%0d out=%0b%0b:%0d | b0=%0b%0b:%0d b1=%0b%0b:%0d join=%0b%0b:%0d acc=%0b%0b:%0d acc_reg=%0d stage=%0b%0b:%0d",
                cycle,
                in0_valid, in0_ready, in0_data,
                in1_valid, in1_ready, in1_data,
                out_valid, out_ready, out_data,
                dut.buf0_out_valid, dut.buf0_out_ready, dut.buf0_out_data,
                dut.buf1_out_valid, dut.buf1_out_ready, dut.buf1_out_data,
                dut.join_out_valid, dut.join_out_ready, dut.join_out_data,
                dut.acc_out_valid, dut.acc_out_ready, dut.acc_out_data,
                dut.accumulator.acc_reg,
                dut.out_stage.pipe_valid, dut.out_stage.out_valid, dut.out_stage.out_data
            );
            if (dut.join_out_valid && dut.join_out_ready) begin
                $display("  JOIN_ACCEPT data=%0d", dut.join_out_data);
            end
            if (out_valid && out_ready) begin
                observed_sum = out_data;
                $display("  OUT_ACCEPT data=%0d", out_data);
            end
        end
    end

    initial begin
        cycle = 0;
        observed_sum = 0;
        reset_n = 0;
        in0_valid = 0;
        in1_valid = 0;
        in0_data = 0;
        in1_data = 0;
        out_ready = 1;

        in0_seq[0] = 8'd10;
        in0_seq[1] = 8'd20;
        in0_seq[2] = 8'd30;
        in0_seq[3] = 8'd40;
        in0_seq[4] = 8'd50;
        in1_seq[0] = 8'd1;
        in1_seq[1] = 8'd2;
        in1_seq[2] = 8'd3;
        in1_seq[3] = 8'd4;
        in1_seq[4] = 8'd5;

        #10;
        reset_n = 1;
        #10;

        for (i = 0; i < 5; i = i + 1) begin
            @(negedge clk);
            in0_valid <= 1;
            in1_valid <= 1;
            in0_data <= in0_seq[i];
            in1_data <= in1_seq[i];
            @(posedge clk);
            while (!(in0_ready && in1_ready)) begin
                @(posedge clk);
            end
            @(negedge clk);
            in0_valid <= 0;
            in1_valid <= 0;
        end

        repeat (16) @(posedge clk);
        $display("TRACE_DONE final_out=%0d acc_reg=%0d expected_all_pairs=165", observed_sum, dut.accumulator.acc_reg);
        $finish;
    end
endmodule
