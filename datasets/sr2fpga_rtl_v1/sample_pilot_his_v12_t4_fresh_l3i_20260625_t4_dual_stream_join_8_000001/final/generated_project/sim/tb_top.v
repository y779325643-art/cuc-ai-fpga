// Self-checking testbench for dual stream join with accumulation
// Assumes priority to in0 in join arbiter
// Compile with iverilog -g2012
module tb_top;

parameter DATA_WIDTH = 8;

reg clk;
reg rst_n;
reg in0_valid, in1_valid;
reg [DATA_WIDTH-1:0] in0_data, in1_data;
wire in0_ready, in1_ready;
wire out_valid;
wire [DATA_WIDTH-1:0] out_data;
reg out_ready;

integer i;
integer errors;
integer timeout;

// DUT instantiation
top #(.DATA_WIDTH(DATA_WIDTH)) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_data(in0_data),
    .in0_ready(in0_ready),
    .in1_valid(in1_valid),
    .in1_data(in1_data),
    .in1_ready(in1_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(out_ready)
);

// Clock generation
always begin
    #5 clk = ~clk;
end

initial begin
    clk = 0;
    rst_n = 0;
    in0_valid = 0;
    in1_valid = 0;
    in0_data = 0;
    in1_data = 0;
    out_ready = 1;
    errors = 0;
    
    // Reset
    #10 rst_n = 1;
    #10;
    
    // Test basic flow
    // Send two values on in0 and one on in1
    // Expected output: first in0 (10), then in0+in1 (10+20=30), then wrap? No overflow yet
    // But note: accumulator outputs after each accumulation, so we expect two outputs: 10 and 30
    // Also, with priority to in0, if both valid simultaneously, in0 goes first
    
    // Send in0=10
    @(negedge clk);
    in0_valid = 1;
    in0_data = 10;
    @(negedge clk);
    // Wait for handshake
    timeout = 0;
    while (!in0_ready && timeout < 100) begin
        @(negedge clk);
        timeout = timeout + 1;
    end
    if (timeout == 100) begin
        $display("TEST_FAIL: Timeout on in0 handshake");
        errors = errors + 1;
    end
    in0_valid = 0;
    
    // Send in1=20
    @(negedge clk);
    in1_valid = 1;
    in1_data = 20;
    @(negedge clk);
    timeout = 0;
    while (!in1_ready && timeout < 100) begin
        @(negedge clk);
        timeout = timeout + 1;
    end
    if (timeout == 100) begin
        $display("TEST_FAIL: Timeout on in1 handshake");
        errors = errors + 1;
    end
    in1_valid = 0;
    
    // Now send another in0=5
    @(negedge clk);
    in0_valid = 1;
    in0_data = 5;
    @(negedge clk);
    timeout = 0;
    while (!in0_ready && timeout < 100) begin
        @(negedge clk);
        timeout = timeout + 1;
    end
    if (timeout == 100) begin
        $display("TEST_FAIL: Timeout on second in0 handshake");
        errors = errors + 1;
    end
    in0_valid = 0;
    
    // Now check outputs: first out_valid should appear with accumulated value 10 (from first in0)
    // Wait for out_valid
    @(posedge clk); #1; // small delay to observe after nonblocking
    timeout = 0;
    while (!out_valid && timeout < 100) begin
        @(posedge clk); #1;
        timeout = timeout + 1;
    end
    if (timeout == 100) begin
        $display("TEST_FAIL: Timeout waiting for first output");
        errors = errors + 1;
    end else begin
        if (out_data !== 8'd10) begin
            $display("TEST_FAIL: Expected first output 10, got %d", out_data);
            errors = errors + 1;
        end else begin
            $display("First output correct: %d", out_data);
        end
        // Accept the output
        @(negedge clk);
        // Next output should be 10+20=30
        timeout = 0;
        while (!out_valid && timeout < 100) begin
            @(posedge clk); #1;
            timeout = timeout + 1;
        end
        if (timeout == 100) begin
            // Might have missed? possible if back-to-back? Check after two cycles
            @(posedge clk); #1;
            if (out_valid) begin
                if (out_data !== 8'd30) begin
                    $display("TEST_FAIL: Expected second output 30, got %d", out_data);
                    errors = errors + 1;
                end else begin
                    $display("Second output correct: %d", out_data);
                end
            end else begin
                $display("TEST_FAIL: Expected second output valid, but not seen");
                errors = errors + 1;
            end
        end else begin
            if (out_data !== 8'd30) begin
                $display("TEST_FAIL: Expected second output 30, got %d", out_data);
                errors = errors + 1;
            end else begin
                $display("Second output correct: %d", out_data);
            end
        end
    end
    
    // Test backpressure: lower out_ready, send more data
    // Send in0=1 and in1=2
    @(negedge clk);
    out_ready = 0;
    in0_valid = 1; in0_data = 1;
    in1_valid = 1; in1_data = 2;
    @(negedge clk);
    // Wait a couple cycles
    repeat (5) @(negedge clk);
    out_ready = 1;
    @(negedge clk);
    // Now check outputs: third output (after second handshake) should be 30+1=31 (if in0 prioritized) then 31+2=33
    // Actually, order: after previous outputs, accumulator had 30. Then in0=1 arrives, accumulator becomes 31, then in1=2, becomes 33.
    // But due to priority, when both valid, in0 goes first, so we expect 31 then 33.
    timeout = 0;
    while (!out_valid && timeout < 100) begin
        @(posedge clk); #1;
        timeout = timeout + 1;
    end
    if (timeout == 100) begin
        $display("TEST_FAIL: Timeout waiting for third output (backpressure test)");
        errors = errors + 1;
    end else begin
        if (out_data !== 8'd31) begin
            $display("TEST_FAIL: Expected third output 31, got %d", out_data);
            errors = errors + 1;
        end else begin
            $display("Third output correct: %d", out_data);
        end
        @(negedge clk);
        // Wait for fourth output
        timeout = 0;
        while (!out_valid && timeout < 100) begin
            @(posedge clk); #1;
            timeout = timeout + 1;
        end
        if (timeout == 100) begin
            $display("TEST_FAIL: Timeout waiting for fourth output");
            errors = errors + 1;
        end else begin
            if (out_data !== 8'd33) begin
                $display("TEST_FAIL: Expected fourth output 33, got %d", out_data);
                errors = errors + 1;
            end else begin
                $display("Fourth output correct: %d", out_data);
            end
        end
    end
    
    // Test reset
    @(negedge clk);
    rst_n = 0;
    #10;
    @(negedge clk);
    rst_n = 1;
    #10;
    if (out_valid !== 0) begin
        $display("TEST_FAIL: Output valid should be low after reset");
        errors = errors + 1;
    end else begin
        $display("Reset test passed");
    end
    
    if (errors == 0) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL with %d errors", errors);
    end
    
    #50 $finish;
end

endmodule
