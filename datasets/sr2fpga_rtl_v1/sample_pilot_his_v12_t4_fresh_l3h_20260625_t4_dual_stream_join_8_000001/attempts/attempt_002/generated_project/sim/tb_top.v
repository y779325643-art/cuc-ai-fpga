`timescale 1ns / 1ps

module tb_top;

    parameter DATA_WIDTH = 8;
    parameter CLK_PERIOD = 10;
    reg clk;
    reg reset_n;
    reg [DATA_WIDTH-1:0] in0_data;
    reg in0_valid;
    wire in0_ready;
    reg [DATA_WIDTH-1:0] in1_data;
    reg in1_valid;
    wire in1_ready;
    wire [DATA_WIDTH-1:0] out_data;
    wire out_valid;
    reg out_ready;

    integer cycle_count;
    integer error_count;
    integer test_case;
    reg [DATA_WIDTH-1:0] expected_seq [0:9];
    integer seq_idx;
    integer timeout;

    top #(
        .DATA_WIDTH(DATA_WIDTH)
    ) dut (
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

    // Clock generation
    always # (CLK_PERIOD/2) clk = ~clk;

    initial begin
        $dumpfile("sim/tb_top.vcd");
        $dumpvars(0, tb_top);

        // Initialize
        clk = 0;
        reset_n = 0;
        in0_data = 0;
        in0_valid = 0;
        in1_data = 0;
        in1_valid = 0;
        out_ready = 1;
        error_count = 0;
        test_case = 0;
        seq_idx = 0;

        // Reset sequence
        #(CLK_PERIOD*2);
        reset_n = 1;
        #(CLK_PERIOD);

        // Test 1: Basic join and accumulate
        test_case = 1;
        $display("Test %0d: Basic join and accumulate", test_case);
        // Define expected sequence: accumulate in0_data only as joined data
        // Joins output in0_data when both valid
        // seq: 1, 1+2=3, 3+3=6, 6+4=10, 10+5=15 (all modulo 256)
        expected_seq[0] = 8'd1;
        expected_seq[1] = 8'd3;
        expected_seq[2] = 8'd6;
        expected_seq[3] = 8'd10;
        expected_seq[4] = 8'd15;
        expected_seq[5] = 8'd21;
        expected_seq[6] = 8'd28;
        expected_seq[7] = 8'd36;
        expected_seq[8] = 8'd45;
        expected_seq[9] = 8'd55;

        // Drive inputs
        fork
            begin
                // Driver for in0: 1,2,3,4,5,6,7,8,9,10
                @(posedge clk); #1;
                in0_data = 8'd1; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd2; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd3; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd4; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd5; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd6; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd7; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd8; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd9; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd10; in0_valid = 1;
                #(CLK_PERIOD); in0_valid = 0;
            end
            begin
                // Driver for in1: always valid with same data as in0? But join uses in0_data only
                // We'll just drive in1 with arbitrary data (100) to make both valid
                repeat(10) @(posedge clk) #1;
                in1_data = 8'd100; in1_valid = 1;
                #(CLK_PERIOD*10);
                in1_valid = 0;
            end
        join

        // Check outputs
        seq_idx = 0;
        timeout = 0;
        while (seq_idx < 10 && timeout < 100) begin
            @(negedge clk);
            if (out_valid && out_ready) begin
                if (out_data !== expected_seq[seq_idx]) begin
                    $display("TEST_FAIL: Mismatch at seq_idx %0d: expected %0d, got %0d", seq_idx, expected_seq[seq_idx], out_data);
                    error_count = error_count + 1;
                end
                seq_idx = seq_idx + 1;
            end
            timeout = timeout + 1;
        end
        if (timeout >= 100) begin
            $display("TEST_FAIL: Timeout waiting for output");
            error_count = error_count + 1;
        end

        // Test 2: Backpressure
        test_case = 2;
        $display("Test %0d: Backpressure scenario", test_case);
        // Reinitialize
        #(CLK_PERIOD*2);
        reset_n = 0;
        #(CLK_PERIOD);
        reset_n = 1;
        #(CLK_PERIOD);

        // Drive inputs with intermittent out_ready
        fork
            begin
                // in0 driver
                @(posedge clk); #1;
                in0_data = 8'd10; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd20; in0_valid = 1;
                @(posedge clk); #1;
                in0_data = 8'd30; in0_valid = 1;
                #(CLK_PERIOD*2);
                in0_valid = 0;
            end
            begin
                // in1 driver
                @(posedge clk); #1;
                in1_data = 8'd1; in1_valid = 1;
                #(CLK_PERIOD*3);
                in1_valid = 0;
            end
            begin
                // out_ready toggling
                #(CLK_PERIOD);
                out_ready = 0;
                #(CLK_PERIOD*3);
                out_ready = 1;
                #(CLK_PERIOD*2);
                out_ready = 0;
                #(CLK_PERIOD);
                out_ready = 1;
            end
        join

        // Expected: accumulate 10, then 10+20=30, then 30+30=60? But due to backpressure, may have delay.
        // Since join only uses in0_data, and in1 is always valid, outputs should be 10,30,60.
        seq_idx = 0;
        expected_seq[0] = 8'd10;
        expected_seq[1] = 8'd30;
        expected_seq[2] = 8'd60;
        timeout = 0;
        while (seq_idx < 3 && timeout < 50) begin
            @(negedge clk);
            if (out_valid && out_ready) begin
                if (out_data !== expected_seq[seq_idx]) begin
                    $display("TEST_FAIL: Test %0d Mismatch at seq_idx %0d: expected %0d, got %0d", test_case, seq_idx, expected_seq[seq_idx], out_data);
                    error_count = error_count + 1;
                end
                seq_idx = seq_idx + 1;
            end
            timeout = timeout + 1;
        end
        if (timeout >= 50) begin
            $display("TEST_FAIL: Test %0d Timeout", test_case);
            error_count = error_count + 1;
        end

        // Conclusion
        #(CLK_PERIOD*2);
        if (error_count == 0) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL: %0d errors", error_count);
        end

        $finish;
    end

endmodule
