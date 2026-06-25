`timescale 1ns/1ps

module tb_top;

    parameter DATA_WIDTH = 8;

    reg clk;
    reg rst_n;

    reg in0_valid;
    wire in0_ready;
    reg [DATA_WIDTH-1:0] in0_data;
    reg in1_valid;
    wire in1_ready;
    reg [DATA_WIDTH-1:0] in1_data;

    wire out_valid;
    reg out_ready;
    wire [DATA_WIDTH-1:0] out_data;

    // DUT
    top #(
        .DATA_WIDTH(DATA_WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
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
    always #5 clk = ~clk;

    // Test stimulus and checker
    integer cycle_count;
    integer i;
    reg [DATA_WIDTH-1:0] expected_out [0:2];
    reg [DATA_WIDTH-1:0] seq0 [0:2];
    reg [DATA_WIDTH-1:0] seq1 [0:2];
    reg test_pass;
    integer num_packets;

    initial begin
        $display("Starting testbench...");
        test_pass = 1;
        num_packets = 3;

        // Initialize sequences
        seq0[0] = 8'd1;
        seq0[1] = 8'd2;
        seq0[2] = 8'd3;
        seq1[0] = 8'd4;
        seq1[1] = 8'd5;
        seq1[2] = 8'd6;

        // Expected outputs after accumulation (sums accumulate)
        expected_out[0] = 8'd1 + 8'd4; // 5
        expected_out[1] = expected_out[0] + 8'd2 + 8'd5; // 5+2+5=12
        expected_out[2] = expected_out[1] + 8'd3 + 8'd6; // 12+3+6=21

        // Initialize signals
        clk = 0;
        rst_n = 0;
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 1; // ready to absorb
        in0_data = 0;
        in1_data = 0;

        // Reset
        #15 rst_n = 1;
        #20;

        // Drive stimulus on negedge
        i = 0;
        cycle_count = 0;
        while (i < num_packets && cycle_count < 100) begin
            @(negedge clk);
            in0_valid = 1;
            in1_valid = 1;
            in0_data = seq0[i];
            in1_data = seq1[i];
            // Wait for handshake
            @(posedge clk);
            // Observe outputs on negedge after posedge
            @(negedge clk);
            // Check if output occurred and expected
            // We'll check in a separate loop for simplicity
            // Wait until out_valid and check
            fork : wait_and_check
                begin
                    wait(out_valid);
                    // Small delay to allow data to settle
                    #1;
                    if (out_data !== expected_out[i]) begin
                        $display("TEST_FAIL at packet %0d: expected %0d, got %0d", i, expected_out[i], out_data);
                        test_pass = 0;
                    end else begin
                        $display("Packet %0d OK: expected %0d, got %0d", i, expected_out[i], out_data);
                    end
                end
            join
            // Release valid
            @(negedge clk);
            in0_valid = 0;
            in1_valid = 0;
            i = i + 1;
            cycle_count = cycle_count + 1;
        end

        if (i < num_packets) begin
            $display("TEST_FAIL: timeout waiting for transfers");
            test_pass = 0;
        end

        // Additional backpressure test
        $display("Backpressure test...");
        // Reset
        @(negedge clk);
        rst_n = 0;
        #20 rst_n = 1;
        #20;

        i = 0;
        cycle_count = 0;
        out_ready = 0; // hold backpressure
        while (i < num_packets && cycle_count < 100) begin
            @(negedge clk);
            in0_valid = 1;
            in1_valid = 1;
            in0_data = seq0[i];
            in1_data = seq1[i];
            // Assert out_ready after some cycles
            if (i == 0) begin
                #30 out_ready = 1;
            end else begin
                #15 out_ready = 1;
            end
            @(posedge clk);
            // Wait for output
            @(negedge clk);
            wait(out_valid);
            #1;
            if (out_data !== expected_out[i]) begin
                $display("TEST_FAIL backpressure packet %0d: expected %0d, got %0d", i, expected_out[i], out_data);
                test_pass = 0;
            end else begin
                $display("Backpressure packet %0d OK", i);
            end
            @(negedge clk);
            in0_valid = 0;
            in1_valid = 0;
            out_ready = 0; // re-assert backpressure for next
            i = i + 1;
            cycle_count = cycle_count + 1;
        end

        if (i < num_packets) begin
            $display("TEST_FAIL: timeout during backpressure test");
            test_pass = 0;
        end

        #100;

        if (test_pass) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL");
        end

        $finish;
    end

endmodule
