`timescale 1ns/1ps
module tb_top;
    reg clk;
    reg rst_n;
    reg event_valid;
    wire [7:0] count;

    top dut (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .count(count)
    );

    always #5 clk = ~clk;

    integer i;
    integer start_time;
    integer timeout;

    initial begin
        $display("Starting testbench");
        clk = 0;
        rst_n = 0;
        event_valid = 0;
        repeat (5) @(negedge clk);
        @(negedge clk) rst_n = 1;
        @(negedge clk);

        if (count !== 8'd0) begin
            $display("ERROR: count not zero after reset, got %d", count);
            $display("TEST_FAIL");
            $finish;
        end

        for (i = 0; i < 10; i = i + 1) begin
            @(negedge clk) event_valid = 1;
            @(negedge clk) event_valid = 0;
            if (count !== i + 1) begin
                $display("ERROR: after pulse %0d, expected count %0d, got %0d", i, i+1, count);
                $display("TEST_FAIL");
                $finish;
            end
        end

        @(negedge clk) event_valid = 1;
        @(negedge clk);
        @(negedge clk) event_valid = 0;
        if (count !== 12) begin
            $display("ERROR: after back-to-back pulses, expected count 12, got %d", count);
            $display("TEST_FAIL");
            $finish;
        end

        @(negedge clk) rst_n = 0;
        repeat (2) @(negedge clk);
        @(negedge clk) rst_n = 1;
        @(negedge clk);
        if (count !== 0) begin
            $display("ERROR: count not reset after second reset, got %d", count);
            $display("TEST_FAIL");
            $finish;
        end

        for (i = 0; i < 5; i = i + 1) begin
            @(negedge clk) event_valid = 1;
            @(negedge clk) event_valid = 0;
            if (count !== i + 1) begin
                $display("ERROR: after pulse %0d, expected count %0d, got %0d", i, i+1, count);
                $display("TEST_FAIL");
                $finish;
            end
        end

        $display("All tests passed.");
        $display("TEST_PASS");
        $finish;
    end

    initial begin
        #100000;
        $display("ERROR: Global timeout reached");
        $display("TEST_FAIL");
        $finish;
    end
endmodule
