// tb_top.v - Self-checking testbench for top module
`timescale 1ns/1ps

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

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

    // Instantiate DUT
    top dut (
        .clk(clk),
        .reset_n(reset_n),
        .in0_data(in0_data),
        .in0_valid(in0_valid),
        .in0_ready(in0_ready),
        .in1_data(in1_data),
        .in1_valid(in1_valid),
        .in1_ready(in1_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );

    // Test sequence
    integer cycle_count;
    reg [7:0] expected_accum;
    reg [7:0] in0_vals [0:4];
    reg [7:0] in1_vals [0:4];
    integer i;

    initial begin
        // Initialize arrays
        in0_vals[0] = 8'd1;
        in0_vals[1] = 8'd2;
        in0_vals[2] = 8'd3;
        in0_vals[3] = 8'd4;
        in0_vals[4] = 8'd5;
        in1_vals[0] = 8'd10;
        in1_vals[1] = 8'd20;
        in1_vals[2] = 8'd30;
        in1_vals[3] = 8'd40;
        in1_vals[4] = 8'd50;

        // Reset
        reset_n = 0;
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 1;  // Keep ready high always to avoid deadlock
        #20 reset_n = 1;
        #10;

        expected_accum = 0;
        cycle_count = 0;

        // Send 5 pairs of data
        for (i = 0; i < 5; i = i + 1) begin
            // Wait until ready
            cycle_count = 0;
            while (!(in0_ready && in1_ready)) begin
                @(posedge clk);
                cycle_count = cycle_count + 1;
                if (cycle_count > 100) begin
                    $display("TEST_FAIL: timeout waiting for ready at iteration %0d", i);
                    $finish;
                end
            end
            // Drive inputs
            in0_data = in0_vals[i];
            in1_data = in1_vals[i];
            in0_valid = 1;
            in1_valid = 1;
            // Wait a cycle
            @(posedge clk);
            in0_valid = 0;
            in1_valid = 0;
            expected_accum = expected_accum + (in0_vals[i] + in1_vals[i]);
            // Wait for output to appear
            cycle_count = 0;
            while (!out_valid) begin
                @(posedge clk);
                cycle_count = cycle_count + 1;
                if (cycle_count > 100) begin
                    $display("TEST_FAIL: timeout waiting for output at iteration %0d", i);
                    $finish;
                end
            end
            // Check output
            if (out_data !== expected_accum) begin
                $display("TEST_FAIL: mismatch at iteration %0d, expected %0d, got %0d", i, expected_accum, out_data);
                $finish;
            end
            // Output is already consumed because out_ready=1, so just wait a cycle to allow pipeline to clear
            @(posedge clk);
        end

        // Wait a few cycles to ensure no extra outputs
        #50;
        if (out_valid) begin
            $display("TEST_FAIL: unexpected output after all data");
            $finish;
        end

        $display("TEST_PASS");
        $finish;
    end

endmodule
