`timescale 1ns/1ps
module tb_top;
reg clk;
reg reset_n;
reg event_valid;
wire [7:0] count;

top dut (
    .clk(clk),
    .reset_n(reset_n),
    .event_valid(event_valid),
    .count(count)
);

// Clock generation
always #5 clk = ~clk;

integer i;
integer expected;

initial begin
    $display("Starting testbench");
    clk = 0;
    reset_n = 0;
    event_valid = 0;
    // Reset for a few cycles
    repeat(5) @(negedge clk);
    reset_n = 1;
    @(negedge clk);

    // Wait for count to be 0 after reset
    if (count !== 8'd0) begin
        $display("TEST_FAIL: count not zero after reset");
        $finish;
    end

    // Test sequence: drive 20 events, check count increments each time
    for (i = 0; i < 20; i = i + 1) begin
        @(negedge clk);
        event_valid = 1;
        @(negedge clk);
        event_valid = 0;
        @(negedge clk);
        expected = i + 1;
        if (count !== expected) begin
            $display("TEST_FAIL: expected count %d, got %d after event %d", expected, count, i);
            $finish;
        end
        else $display("Count ok: %d", count);
    end

    // Now test wrap-around
    expected = 20;
    for (i = 0; i < 236; i = i + 1) begin
        @(negedge clk);
        event_valid = 1;
        @(negedge clk);
        event_valid = 0;
        @(negedge clk);
        expected = (expected + 1) % 256;
        if (count !== expected) begin
            $display("TEST_FAIL: expected count %d, got %d at wrap test step %d", expected, count, i);
            $finish;
        end
        else $display("Count wrap ok: %d", count);
    end

    $display("TEST_PASS");
    $finish;
end

// Timeout watchdog
initial begin
    #1000000;
    $display("TEST_FAIL: timeout");
    $finish;
end

endmodule
