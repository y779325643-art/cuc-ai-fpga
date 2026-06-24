module tb_top;

reg clk;
reg reset_n;
reg event_valid;
wire [7:0] count;

integer errors;

// Instantiate DUT
top u_top (
    .clk(clk),
    .reset_n(reset_n),
    .event_valid(event_valid),
    .count(count)
);

// Clock generation
always #5 clk = ~clk;

initial begin
    // Initialize
    clk = 0;
    reset_n = 0;
    event_valid = 0;
    errors = 0;
    #10 reset_n = 1;
    #10;
    
    // Test 1: No events, count should stay 0
    #20;
    if (count !== 8'd0) begin
        $display("FAIL: Test 1 - count expected 0, got %d", count);
        errors = errors + 1;
    end
    
    // Test 2: Single event
    event_valid = 1;
    #10;
    event_valid = 0;
    #10;
    if (count !== 8'd1) begin
        $display("FAIL: Test 2 - count expected 1, got %d", count);
        errors = errors + 1;
    end
    
    // Test 3: Multiple events
    event_valid = 1;
    #10;
    event_valid = 0;
    #10;
    event_valid = 1;
    #10;
    event_valid = 0;
    #10;
    event_valid = 1;
    #10;
    event_valid = 0;
    #10;
    if (count !== 8'd4) begin
        $display("FAIL: Test 3 - count expected 4, got %d", count);
        errors = errors + 1;
    end
    
    // Test 4: Reset
    reset_n = 0;
    #10;
    reset_n = 1;
    #10;
    if (count !== 8'd0) begin
        $display("FAIL: Test 4 - count expected 0 after reset, got %d", count);
        errors = errors + 1;
    end
    
    // Test 5: Overflow check (send 256 events to wrap around)
    event_valid = 0;
    repeat (256) begin
        @(posedge clk);
        event_valid = 1;
        @(posedge clk);
        event_valid = 0;
    end
    @(posedge clk);
    // After 256 events, count should be 0 (wrapped)
    if (count !== 8'd0) begin
        $display("FAIL: Test 5 - count expected 0 after 256 events, got %d", count);
        errors = errors + 1;
    end
    
    // Final result
    if (errors === 0) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL");
    end
    #10 $finish;
end

endmodule
