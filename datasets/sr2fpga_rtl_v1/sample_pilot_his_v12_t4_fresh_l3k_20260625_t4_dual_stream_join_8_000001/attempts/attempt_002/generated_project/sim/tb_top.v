// Self-checking testbench for top module
`timescale 1ns / 1ps

module tb_top;

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

    // Clock generation
    always #5 clk = ~clk;

    // Test variables
    integer test_failed;
    integer timeout_count;
    reg [7:0] expected_acc;
    reg [7:0] in0_seq [0:4];
    reg [7:0] in1_seq [0:4];
    reg [7:0] out_seq [0:4];
    integer i;

    initial begin
        clk = 0;
        reset_n = 0;
        in0_data = 0;
        in0_valid = 0;
        in1_data = 0;
        in1_valid = 0;
        out_ready = 0;
        test_failed = 0;

        // Initialize sequences
        in0_seq[0] = 8'd10; in0_seq[1] = 8'd20; in0_seq[2] = 8'd30; in0_seq[3] = 8'd40; in0_seq[4] = 8'd50;
        in1_seq[0] = 8'd1; in1_seq[1] = 8'd2; in1_seq[2] = 8'd3; in1_seq[3] = 8'd4; in1_seq[4] = 8'd5;
        expected_acc = 0;

        // Reset
        #10 reset_n = 1;
        #10;

        // Test 1: Basic back-to-back transfers
        $display("Starting basic test...");
        out_ready = 1;
        for (i = 0; i < 5; i = i + 1) begin
            // Drive inputs on negedge
            @(negedge clk);
            in0_data = in0_seq[i];
            in0_valid = 1;
            in1_data = in1_seq[i];
            in1_valid = 1;
            // Wait for output valid
            timeout_count = 0;
            while (~out_valid) begin
                @(posedge clk);
                timeout_count = timeout_count + 1;
                if (timeout_count > 100) begin
                    $display("TEST_FAIL: Timeout waiting for out_valid");
                    test_failed = 1;
                    $finish;
                end
                #1; // small delay after posedge
            end
            // Check output on negedge after valid
            @(negedge clk);
            expected_acc = expected_acc + (in0_seq[i] + in1_seq[i]);
            if (out_data !== expected_acc) begin
                $display("TEST_FAIL: Mismatch at transfer %0d, expected %0d, got %0d", i, expected_acc, out_data);
                test_failed = 1;
            end
            // Deassert valid after handshake (ready asserted)
            @(negedge clk);
            in0_valid = 0;
            in1_valid = 0;
        end
        // Wait for pipeline to flush
        repeat (5) @(posedge clk);
        #1;

        // Test 2: Backpressure
        $display("Starting backpressure test...");
        out_ready = 0;
        // Send one transfer
        @(negedge clk);
        in0_data = 8'd100;
        in0_valid = 1;
        in1_data = 8'd200;
        in1_valid = 1;
        // Wait a few cycles with out_ready low
        repeat (3) @(posedge clk);
        // Assert out_ready
        @(negedge clk);
        out_ready = 1;
        // Wait for output
        timeout_count = 0;
        while (~out_valid) begin
            @(posedge clk);
            timeout_count = timeout_count + 1;
            if (timeout_count > 100) begin
                $display("TEST_FAIL: Timeout during backpressure test");
                test_failed = 1;
                $finish;
            end
            #1;
        end
        @(negedge clk);
        expected_acc = expected_acc + (8'd100 + 8'd200);
        if (out_data !== expected_acc) begin
            $display("TEST_FAIL: Backpressure mismatch, expected %0d, got %0d", expected_acc, out_data);
            test_failed = 1;
        end
        @(negedge clk);
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 0;
        // Flush
        repeat (5) @(posedge clk);
        #1;

        // Test 3: Reset verification
        $display("Starting reset test...");
        @(negedge clk);
        reset_n = 0;
        #10;
        reset_n = 1;
        #10;
        // Send a new sample
        @(negedge clk);
        in0_data = 8'd1;
        in0_valid = 1;
        in1_data = 8'd2;
        in1_valid = 1;
        out_ready = 1;
        timeout_count = 0;
        while (~out_valid) begin
            @(posedge clk);
            timeout_count = timeout_count + 1;
            if (timeout_count > 100) begin
                $display("TEST_FAIL: Timeout after reset");
                test_failed = 1;
                $finish;
            end
            #1;
        end
        @(negedge clk);
        if (out_data !== 8'd3) begin // 1+2=3, accumulator should be 0 after reset
            $display("TEST_FAIL: After reset expected 3, got %0d", out_data);
            test_failed = 1;
        end
        @(negedge clk);
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 0;

        // Final result
        #50;
        if (test_failed) begin
            $display("TEST_FAIL");
        end else begin
            $display("TEST_PASS");
        end
        $finish;
    end

endmodule
