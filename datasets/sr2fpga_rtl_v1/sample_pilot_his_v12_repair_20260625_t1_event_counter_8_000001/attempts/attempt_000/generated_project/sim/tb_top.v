////////////////////////////////////////////////////////////////////////////////
// tb_top.v
// Self-checking testbench for event counter.
// Applies a sequence of event pulses and verifies count and count_valid.
////////////////////////////////////////////////////////////////////////////////

`timescale 1ns / 1ps

module tb_top;

    reg  clk;
    reg  rst_n;
    reg  event_in;
    wire [7:0] count;
    wire count_valid;

    // Clock generation: 100 MHz -> period 10 ns
    always #5 clk = ~clk;

    // Instantiate DUT
    top dut (
        .clk         (clk),
        .rst_n       (rst_n),
        .event_in    (event_in),
        .count       (count),
        .count_valid (count_valid)
    );

    // Test sequence
    initial begin
        // Initialize
        clk = 0;
        rst_n = 0;
        event_in = 0;
        #20;
        rst_n = 1;
        #10;

        // Check initial state
        if (count !== 8'd0 || count_valid !== 1'b0) begin
            $display("TEST_FAIL: initial values");
            $finish;
        end

        // Apply 5 event pulses, each spaced 3 clock cycles apart
        repeat (5) begin
            @(posedge clk);
            event_in = 1;
            @(posedge clk);
            event_in = 0;
            // Wait for outputs to settle (should be ready at next posedge)
            @(posedge clk);
            // Check count_valid should be 1 for the pulse, then 0
            if (count_valid !== 1'b1) begin
                $display("TEST_FAIL: count_valid not asserted after event");
                $finish;
            end
            @(posedge clk);
            if (count_valid !== 1'b0) begin
                $display("TEST_FAIL: count_valid not deasserted");
                $finish;
            end
        end

        // After 5 pulses, count should be 5
        if (count !== 8'd5) begin
            $display("TEST_FAIL: count = %d, expected 5", count);
            $finish;
        end

        // Test overflow: apply 251 more pulses to reach 256 -> 0
        repeat (251) begin
            @(posedge clk);
            event_in = 1;
            @(posedge clk);
            event_in = 0;
            @(posedge clk);
            @(posedge clk);
        end

        // Now count should be 0 (256 total pulses, 8-bit wrap)
        if (count !== 8'd0) begin
            $display("TEST_FAIL: overflow test, count = %d, expected 0", count);
            $finish;
        end

        // Apply one more pulse to verify count becomes 1
        @(posedge clk);
        event_in = 1;
        @(posedge clk);
        event_in = 0;
        @(posedge clk);
        @(posedge clk);
        if (count !== 8'd1 || count_valid !== 1'b0) begin
            $display("TEST_FAIL: final pulse, count = %d, expected 1", count);
            $finish;
        end

        $display("TEST_PASS");
        $finish;
    end

endmodule
