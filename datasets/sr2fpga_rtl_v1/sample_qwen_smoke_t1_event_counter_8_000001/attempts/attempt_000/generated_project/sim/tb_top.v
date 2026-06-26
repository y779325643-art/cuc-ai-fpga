// tb_top.v - Self-checking testbench for top event counter
// Compiles with: iverilog -g2012

`timescale 1ns / 1ps

module tb_top;

    parameter DATA_WIDTH = 8;
    parameter CLK_PERIOD = 10;

    reg                  clk;
    reg                  rst_n;
    reg                  event_in;
    wire [DATA_WIDTH-1:0] count_out;

    integer cycle_cnt;
    integer err_cnt;
    integer i;

    // DUT instantiation
    top #(
        .DATA_WIDTH (DATA_WIDTH)
    ) dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .event_in  (event_in),
        .count_out (count_out)
    );

    // Clock generation
    initial begin
        clk = 1'b0;
    end
    always #(CLK_PERIOD/2) clk = ~clk;

    // Monitor for timeout
    always @(posedge clk) begin
        cycle_cnt <= cycle_cnt + 1;
        if (cycle_cnt > 500) begin
            $display("TEST_FAIL: Simulation timeout at cycle %0d", cycle_cnt);
            $finish;
        end
    end

    // Helper task: send a single event pulse for one clock cycle
    task send_event_pulse;
        begin
            @(negedge clk);
            event_in = 1'b1;
            @(negedge clk);
            event_in = 1'b0;
        end
    endtask

    // Helper task: check count value
    task check_count;
        input [DATA_WIDTH-1:0] expected;
        begin
            @(negedge clk);
            if (count_out !== expected) begin
                $display("TEST_FAIL: Expected count %0d, got %0d at cycle %0d",
                         expected, count_out, cycle_cnt);
                err_cnt = err_cnt + 1;
            end else begin
                $display("INFO: Count check passed: %0d == %0d", count_out, expected);
            end
        end
    endtask

    // Main test sequence
    initial begin
        $display("=== Event Counter Testbench Start ===");
        cycle_cnt = 0;
        err_cnt   = 0;
        rst_n     = 1'b0;
        event_in  = 1'b0;

        // Hold reset for a few cycles
        repeat (5) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        // Wait a cycle after reset release
        repeat (2) @(posedge clk);

        // ============================================
        // Scenario 1: basic_count - Send 5 pulses, verify count is 5
        // ============================================
        $display("--- Scenario 1: basic_count ---");

        for (i = 0; i < 5; i = i + 1) begin
            send_event_pulse;
        end

        // Allow one cycle for the last increment to settle
        @(negedge clk);

        check_count(8'd5);

        // ============================================
        // Scenario 2: reset_test - Assert reset, verify count is 0
        // ============================================
        $display("--- Scenario 2: reset_test ---");

        // Assert reset synchronously
        @(negedge clk);
        rst_n = 1'b0;

        // Wait for reset to take effect
        repeat (3) @(posedge clk);
        @(negedge clk);

        check_count(8'd0);

        // Release reset
        rst_n = 1'b1;
        repeat (2) @(posedge clk);

        // Verify counter still at 0 after reset release
        check_count(8'd0);

        // ============================================
        // Additional: Send 3 more pulses after reset
        // ============================================
        $display("--- Additional: 3 pulses after reset ---");

        for (i = 0; i < 3; i = i + 1) begin
            send_event_pulse;
        end

        @(negedge clk);
        check_count(8'd3);

        // ============================================
        // Final result
        // ============================================
        repeat (3) @(posedge clk);

        if (err_cnt == 0) begin
            $display("=== TEST_PASS ===");
        end else begin
            $display("=== TEST_FAIL: %0d errors detected ===", err_cnt);
        end

        $finish;
    end

endmodule
