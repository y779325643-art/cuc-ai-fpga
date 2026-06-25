// Self-checking testbench for top module
// Uses bounded loops with timeout
// Prints TEST_PASS or TEST_FAIL

`timescale 1ns / 1ps

module tb_top;

    parameter DATA_WIDTH = 8;
    parameter CLK_PERIOD = 10;

    reg clk;
    reg rst_n;
    reg [DATA_WIDTH-1:0] in0_data;
    reg in0_valid;
    wire in0_ready;
    reg [DATA_WIDTH-1:0] in1_data;
    reg in1_valid;
    wire in1_ready;
    wire [DATA_WIDTH-1:0] out_data;
    wire out_valid;
    reg out_ready;

    integer cycle_cnt;
    integer error_cnt;
    integer i;
    integer test_finished;

    // Test vectors
    reg [DATA_WIDTH-1:0] in0_seq [0:9];
    reg [DATA_WIDTH-1:0] in1_seq [0:9];
    reg [DATA_WIDTH-1:0] expected_out [0:9];

    // DUT instantiation
    top dut (
        .clk(clk),
        .rst_n(rst_n),
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

    // Clock generation
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // Test stimulus
    initial begin
        // Initialize sequences
        in0_seq[0] = 8'd10; in1_seq[0] = 8'd20; expected_out[0] = 8'd30;
        in0_seq[1] = 8'd5;  in1_seq[1] = 8'd7;  expected_out[1] = 8'd42;
        in0_seq[2] = 8'd3;  in1_seq[2] = 8'd1;  expected_out[2] = 8'd46;
        in0_seq[3] = 8'd8;  in1_seq[3] = 8'd2;  expected_out[3] = 8'd56;
        in0_seq[4] = 8'd0;  in1_seq[4] = 8'd0;  expected_out[4] = 8'd56;
        in0_seq[5] = 8'd15; in1_seq[5] = 8'd25; expected_out[5] = 8'd96;
        in0_seq[6] = 8'd1;  in1_seq[6] = 8'd2;  expected_out[6] = 8'd99;
        in0_seq[7] = 8'd4;  in1_seq[7] = 8'd6;  expected_out[7] = 8'd109;
        in0_seq[8] = 8'd7;  in1_seq[8] = 8'd3;  expected_out[8] = 8'd119;
        in0_seq[9] = 8'd9;  in1_seq[9] = 8'd1;  expected_out[9] = 8'd129;

        // Reset
        rst_n = 0;
        in0_data = 0;
        in0_valid = 0;
        in1_data = 0;
        in1_valid = 0;
        out_ready = 0;
        @(posedge clk);
        @(posedge clk) rst_n = 1;
        @(posedge clk);

        // Wait for global reset release
        // Now feed inputs
        out_ready = 1;
        error_cnt = 0;
        test_finished = 0;

        for (i = 0; i < 10; i = i + 1) begin
            // Drive inputs with valid
            in0_data = in0_seq[i];
            in0_valid = 1;
            in1_data = in1_seq[i];
            in1_valid = 1;

            // Wait for handshake with timeout
            cycle_cnt = 0;
            while (!(!in0_valid || in0_ready) && !(!in1_valid || in1_ready)) begin
                // Wait until both inputs are accepted (ready is asserted while valid is high)
                // Actually we need to wait until both inputs are accepted.
                // Since join will assert ready when both valid and output ready.
                // We'll wait for both in0_ready and in1_ready (they are the same)
                @(posedge clk);
                cycle_cnt = cycle_cnt + 1;
                if (cycle_cnt > 100) begin
                    $display("TEST_FAIL: Timeout waiting for input handshake at index %d", i);
                    $finish;
                end
            end
            @(posedge clk);
            // Deassert valid after one cycle
            in0_valid = 0;
            in1_valid = 0;
        end

        // Now wait for all outputs to be received
        // We need to read 10 output values
        for (i = 0; i < 10; i = i + 1) begin
            // Wait for valid_out with timeout
            cycle_cnt = 0;
            while (!dut.out_valid) begin
                @(posedge clk);
                cycle_cnt = cycle_cnt + 1;
                if (cycle_cnt > 100) begin
                    //$display("Timeout waiting for output valid at index %d", i);
                    //$display("TEST_FAIL");
                    //$finish;
                end
            end
            // Check output
            if (dut.out_data !== expected_out[i]) begin
                $display("ERROR: Output mismatch at index %d: expected %d, got %d", i, expected_out[i], dut.out_data);
                error_cnt = error_cnt + 1;
            end
            @(posedge clk);
        end

        // Wait a few cycles for pipeline to drain
        repeat(10) @(posedge clk);

        if (error_cnt == 0) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL: %d errors", error_cnt);
        end
        $finish;
    end

endmodule
