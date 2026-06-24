module tb_top;

parameter WIDTH=8;

reg clk, rst_n;
reg in_valid;
reg [WIDTH-1:0] in_data;
wire out0_valid, out1_valid;
wire [WIDTH-1:0] out0_data, out1_data;
reg out0_ready, out1_ready;

integer i;
reg [7:0] expected0 [0:9];
reg [7:0] expected1 [0:9];
integer idx0, idx1;
reg test_pass;

// DUT
 top #(.WIDTH(WIDTH)) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .out0_valid(out0_valid),
    .out0_data(out0_data),
    .out1_valid(out1_valid),
    .out1_data(out1_data),
    .out0_ready(out0_ready),
    .out1_ready(out1_ready)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

initial begin
    // Initialize
    rst_n = 0;
    in_valid = 0;
    in_data = 0;
    out0_ready = 0;
    out1_ready = 0;
    idx0 = 0;
    idx1 = 0;
    test_pass = 1;

    // Reset
    #10 rst_n = 1;
    #10;

    // Load expected data
    for (i=0; i<10; i=i+1) begin
        expected0[i] = i;
        expected1[i] = i;
    end

    // Test sequence: send data with backpressure
    // Send 0..9
    for (i=0; i<10; i=i+1) begin
        @(posedge clk);
        #1; // small delay
        in_valid = 1;
        in_data = i;
        // Random ready behavior
        out0_ready = (i % 2 == 0) ? 1 : 0;
        out1_ready = (i % 2 == 0) ? 1 : 0;
        @(posedge clk);
        #1;
        in_valid = 0;
        // Check outputs when valid
        if (out0_valid && out0_ready) begin
            if (out0_data != expected0[idx0]) begin
                $display("FAIL: out0 mismatch at idx %0d: expected %0d, got %0d", idx0, expected0[idx0], out0_data);
                test_pass = 0;
            end
            idx0 = idx0 + 1;
        end
        if (out1_valid && out1_ready) begin
            if (out1_data != expected1[idx1]) begin
                $display("FAIL: out1 mismatch at idx %0d: expected %0d, got %0d", idx1, expected1[idx1], out1_data);
                test_pass = 0;
            end
            idx1 = idx1 + 1;
        end
        // Random ready for next cycles
        #10;
    end

    // Drain remaining outputs
    repeat (10) begin
        @(posedge clk);
        #1;
        out0_ready = 1;
        out1_ready = 1;
        if (out0_valid) begin
            if (out0_data != expected0[idx0]) begin
                $display("FAIL: out0 mismatch at idx %0d: expected %0d, got %0d", idx0, expected0[idx0], out0_data);
                test_pass = 0;
            end
            idx0 = idx0 + 1;
        end
        if (out1_valid) begin
            if (out1_data != expected1[idx1]) begin
                $display("FAIL: out1 mismatch at idx %0d: expected %0d, got %0d", idx1, expected1[idx1], out1_data);
                test_pass = 0;
            end
            idx1 = idx1 + 1;
        end
        #10;
    end

    // Final check
    if (test_pass && idx0==10 && idx1==10) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL");
    end
    $finish;
end

endmodule
