`timescale 1ns/1ps

module tb_top;
    reg clk;
    reg rst_n;
    reg event_valid;
    wire [7:0] count;

    top uut (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .count(count)
    );

    always #5 clk = ~clk;

    initial begin
        $monitor("Time=%0t, clk=%b, rst_n=%b, event_valid=%b, count=%d", $time, clk, rst_n, event_valid, count);
        clk = 0;
        rst_n = 0;
        event_valid = 0;

        // reset sequence
        #20 rst_n = 1;

        // Check count after reset
        @(negedge clk);
        if (count !== 0) begin
            $display("TEST_FAIL: After reset count not 0, got %d", count);
            $finish;
        end

        // Generate 10 event pulses and check increment
        for (integer i = 0; i < 10; i = i + 1) begin
            // Pulse event_valid for one cycle on negedge
            @(negedge clk);
            event_valid = 1;
            @(negedge clk);
            event_valid = 0;
            // Wait some cycles for counter to update, then check
            repeat(2) @(negedge clk);
            if (count !== i + 1) begin
                $display("TEST_FAIL: After pulse %0d, count=%d, expected %0d", i, count, i+1);
                $finish;
            end
        end

        // Check that count stays stable when no event_valid
        repeat(5) @(negedge clk);
        if (count !== 10) begin
            $display("TEST_FAIL: Count changed without event_valid, got %d", count);
            $finish;
        end

        // Timeout protection: if we reach here, test passes
        $display("TEST_PASS");
        $finish;
    end

    // Global timeout
    initial begin
        #10000;
        $display("TEST_FAIL: Timeout");
        $finish;
    end
endmodule
