`timescale 1ns / 1ps

module tb_top;

    reg clk;
    reg rst_n;
    reg event_valid;
    wire [7:0] count;

    // Expected count value after test
    integer expected;
    integer num_pulses = 5;

    // Device under test
    top dut (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .count(count)
    );

    // Clock generation: 100 MHz -> period 10 ns
    always #5 clk = ~clk;

    initial begin
        // Initialize
        clk = 0;
        rst_n = 0;
        event_valid = 0;
        expected = 0;

        // Reset
        #10 rst_n = 1;
        #10;

        // Apply num_pulses pulses on event_valid
        repeat (num_pulses) begin
            event_valid = 1;
            #10; // hold for one clock cycle
            event_valid = 0;
            #10; // wait one cycle between pulses
        end

        // Wait for pipeline delay (two clock cycles)
        #20;

        // Check count
        if (count == num_pulses) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL: expected %d, got %d", num_pulses, count);
        end

        #10 $finish;
    end

endmodule
