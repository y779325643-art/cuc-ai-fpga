module tb_top;
    reg clk;
    reg rst_n;
    reg in_valid;
    reg [7:0] in_data;
    wire in_ready;
    wire out0_valid;
    wire [7:0] out0_data;
    reg out0_ready;
    wire out1_valid;
    wire [7:0] out1_data;
    reg out1_ready;

    top dut (.*);

    parameter NUM_TRANS = 200;
    reg [7:0] expected [0:NUM_TRANS-1];
    integer send_idx, recv0_idx, recv1_idx;
    integer i;

    // Clock
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset and main stimulus
    initial begin
        rst_n = 0;
        in_valid = 0;
        in_data = 0;
        out0_ready = 1;
        out1_ready = 1;
        send_idx = 0;
        recv0_idx = 0;
        recv1_idx = 0;

        // Populate expected data with random values
        for (i = 0; i < NUM_TRANS; i = i + 1) begin
            expected[i] = $random & 8'hFF;
        end

        // De-assert reset after 10 cycles
        repeat (10) @(negedge clk);
        rst_n = 1;

        fork
            // Send transactions
            begin : send_proc
                for (send_idx = 0; send_idx < NUM_TRANS; send_idx = send_idx + 1) begin
                    // Wait for in_ready
                    while (!in_ready) @(negedge clk);
                    // Drive valid and data on negedge
                    @(negedge clk);
                    in_valid = 1;
                    in_data = expected[send_idx];
                    // Wait for handshake to be sampled (posedge)
                    @(posedge clk);
                    // De-assert valid on next negedge
                    @(negedge clk);
                    in_valid = 0;
                end
            end

            // Receive on out0
            begin : recv0_proc
                while (recv0_idx < NUM_TRANS) begin
                    @(negedge clk);
                    if (out0_valid && out0_ready) begin
                        if (out0_data !== expected[recv0_idx]) begin
                            $display("TEST_FAIL: out0 data mismatch at index %d: expected %h, got %h", recv0_idx, expected[recv0_idx], out0_data);
                            $finish;
                        end
                        recv0_idx = recv0_idx + 1;
                    end
                end
            end

            // Receive on out1
            begin : recv1_proc
                while (recv1_idx < NUM_TRANS) begin
                    @(negedge clk);
                    if (out1_valid && out1_ready) begin
                        if (out1_data !== expected[recv1_idx]) begin
                            $display("TEST_FAIL: out1 data mismatch at index %d: expected %h, got %h", recv1_idx, expected[recv1_idx], out1_data);
                            $finish;
                        end
                        recv1_idx = recv1_idx + 1;
                    end
                end
            end

            // Randomly deassert ready to exercise backpressure
            begin : ready_proc
                while (send_idx < NUM_TRANS || recv0_idx < NUM_TRANS || recv1_idx < NUM_TRANS) begin
                    @(negedge clk);
                    out0_ready = $random % 2;
                    out1_ready = $random % 2;
                end
            end
        join

        if (recv0_idx == NUM_TRANS && recv1_idx == NUM_TRANS)
            $display("TEST_PASS");
        else
            $display("TEST_FAIL: Incomplete reception");
        $finish;
    end

    // Timeout watchdog
    integer timeout;
    initial begin
        timeout = 0;
        while (timeout < 50000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        $display("TEST_FAIL: Timeout");
        $finish;
    end
endmodule
