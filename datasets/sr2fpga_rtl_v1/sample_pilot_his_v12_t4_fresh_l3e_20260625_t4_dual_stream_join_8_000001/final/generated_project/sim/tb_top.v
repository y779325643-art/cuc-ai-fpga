module tb_top;

    reg clk;
    reg reset_n;
    reg [7:0] in0_data;
    reg in0_valid;
    wire in0_ready;
    reg [7:0] in1_data;
    reg in1_valid;
    wire in1_ready;
    wire [7:0] out_data;
    wire out_valid;
    reg out_ready;

    integer cycle_count;
    reg [7:0] expected_sum;
    integer test_fail;

    // Stimulus sequences
    reg [7:0] in0_seq [0:4];
    reg [7:0] in1_seq [0:4];
    integer seq_len;

    // DUT instantiation
    top dut (
        .clk(clk),
        .reset_n(reset_n),
        .in0_valid(in0_valid),
        .in0_ready(in0_ready),
        .in0_data(in0_data),
        .in1_valid(in1_valid),
        .in1_ready(in1_ready),
        .in1_data(in1_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_data(out_data)
    );

    // Clock generation
    always #5 clk = ~clk;  // 10 ns period, 100 MHz

    // Test sequence
    initial begin
        // Initialize
        clk = 0;
        reset_n = 0;
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 1;  // FIX: set to 1, not 2
        in0_data = 0;
        in1_data = 0;
        test_fail = 0;
        expected_sum = 0;
        seq_len = 5;

        // Initialize sequences (avoid aggregate literals)
        in0_seq[0] = 8'd10;
        in0_seq[1] = 8'd20;
        in0_seq[2] = 8'd30;
        in0_seq[3] = 8'd40;
        in0_seq[4] = 8'd50;
        in1_seq[0] = 8'd1;
        in1_seq[1] = 8'd2;
        in1_seq[2] = 8'd3;
        in1_seq[3] = 8'd4;
        in1_seq[4] = 8'd5;

        // Reset
        #10;
        reset_n = 1;
        #10;

        // Drive inputs
        for (integer i = 0; i < seq_len; i = i + 1) begin
            @(negedge clk);
            in0_valid <= 1;
            in1_valid <= 1;
            in0_data <= in0_seq[i];
            in1_data <= in1_seq[i];
            // Wait for handshake on posedge
            @(posedge clk);
            cycle_count = 0;
            while (!(in0_ready && in1_ready)) begin
                @(posedge clk);
                cycle_count = cycle_count + 1;
                if (cycle_count > 100) begin
                    $display("TEST_FAIL: Timeout waiting for input handshake at i=%0d", i);
                    test_fail = 1;
                    $finish;
                end
            end
            expected_sum = expected_sum + (in0_seq[i] + in1_seq[i]);  // accumulate expected
            // Deassert valid after handshake
            @(negedge clk);
            in0_valid <= 0;
            in1_valid <= 0;
        end

        // Wait for all outputs to appear (allow pipeline to drain)
        #50;

        // Check final output value
        @(posedge clk);
        if (out_valid && out_data !== expected_sum[7:0]) begin
            $display("TEST_FAIL: Expected %d but got %d", expected_sum[7:0], out_data);
            test_fail = 1;
        end else if (out_valid) begin
            $display("TEST_PASS: Final output matches expected %d", expected_sum[7:0]);
        end else begin
            // If not valid, maybe need more cycles; do a final check
            @(posedge clk);
            if (out_valid && out_data !== expected_sum[7:0]) begin
                $display("TEST_FAIL: Expected %d but got %d", expected_sum[7:0], out_data);
                test_fail = 1;
            end else if (out_valid) begin
                $display("TEST_PASS: Final output matches expected %d", expected_sum[7:0]);
            end else begin
                $display("TEST_FAIL: No valid output");
                test_fail = 1;
            end
        end

        if (!test_fail) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL");
        end
        $finish;
    end

endmodule
