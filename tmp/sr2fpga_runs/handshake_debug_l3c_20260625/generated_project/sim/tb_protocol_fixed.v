`timescale 1ns/1ps

module tb_protocol_fixed;
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

    integer cycle_count;
    integer i;
    reg [7:0] expected_accum;
    reg [7:0] in0_vals [0:4];
    reg [7:0] in1_vals [0:4];

    initial begin
        in0_vals[0] = 8'd1;
        in0_vals[1] = 8'd2;
        in0_vals[2] = 8'd3;
        in0_vals[3] = 8'd4;
        in0_vals[4] = 8'd5;
        in1_vals[0] = 8'd10;
        in1_vals[1] = 8'd20;
        in1_vals[2] = 8'd30;
        in1_vals[3] = 8'd40;
        in1_vals[4] = 8'd50;

        reset_n = 0;
        in0_data = 0;
        in1_data = 0;
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 1;

        repeat (2) @(posedge clk);
        @(negedge clk);
        reset_n = 1;
        expected_accum = 0;

        for (i = 0; i < 5; i = i + 1) begin
            cycle_count = 0;
            while (!(in0_ready && in1_ready)) begin
                @(negedge clk);
                cycle_count = cycle_count + 1;
                if (cycle_count > 100) begin
                    $display("TEST_FAIL: timeout waiting for ready at iteration %0d", i);
                    $finish;
                end
            end

            in0_data = in0_vals[i];
            in1_data = in1_vals[i];
            in0_valid = 1;
            in1_valid = 1;
            @(posedge clk);
            @(negedge clk);
            in0_valid = 0;
            in1_valid = 0;

            expected_accum = expected_accum + (in0_vals[i] + in1_vals[i]);
            cycle_count = 0;
            while (!out_valid) begin
                @(negedge clk);
                cycle_count = cycle_count + 1;
                if (cycle_count > 100) begin
                    $display("TEST_FAIL: timeout waiting for output at iteration %0d", i);
                    $finish;
                end
            end

            if (out_data !== expected_accum) begin
                $display("TEST_FAIL: mismatch at iteration %0d, expected %0d, got %0d", i, expected_accum, out_data);
                $finish;
            end
        end

        repeat (5) @(posedge clk);
        $display("TEST_PASS");
        $finish;
    end
endmodule
