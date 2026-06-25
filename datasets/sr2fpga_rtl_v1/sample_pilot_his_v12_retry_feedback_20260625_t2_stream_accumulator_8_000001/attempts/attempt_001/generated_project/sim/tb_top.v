`timescale 1ns / 1ps
module tb_top;

    reg clk;
    reg rst_n;
    reg [7:0] test_data [0:4];
    integer i;
    reg [7:0] expected_sum;
    reg [7:0] result;
    reg [3:0] test_cnt;
    reg pass;

    // DUT signals
    wire in_ready;
    reg in_valid;
    reg [7:0] in_data;
    wire out_valid;
    reg out_ready;
    wire [7:0] out_data;

    // Instantiate DUT
    top uut (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_data(in_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_data(out_data)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Test sequence
    initial begin
        // Initialize
        rst_n = 0;
        in_valid = 0;
        in_data = 0;
        out_ready = 0;
        pass = 1'b1;
        test_cnt = 0;
        expected_sum = 0;

        // Reset
        #10;
        rst_n = 1;
        #10;

        // Test 1: Basic accumulation
        test_data[0] = 8'd10;
        test_data[1] = 8'd20;
        test_data[2] = 8'd30;
        test_data[3] = 8'd40;
        test_data[4] = 8'd50;
        expected_sum = 8'd150; // 10+20+30+40+50 = 150 (0x96)

        // Send data with handshake
        for (i = 0; i < 5; i = i + 1) begin
            @(posedge clk);
            #1;
            in_valid <= 1'b1;
            in_data <= test_data[i];
            out_ready <= 1'b1;
            wait (in_ready && in_valid);
            @(posedge clk);
            #1;
            in_valid <= 1'b0;
            in_data <= 8'b0;
        end

        // Wait for output
        @(posedge clk);
        #1;
        if (out_valid) begin
            result = out_data;
            if (result !== expected_sum) begin
                $display("FAIL: Expected %d, got %d", expected_sum, result);
                pass = 1'b0;
            end else begin
                $display("Test 1 Pass: Accumulated = %d", result);
            end
        end else begin
            $display("FAIL: No output after 5 inputs");
            pass = 1'b0;
        end

        // Test 2: Backpressure - intermittent out_ready
        // Reset
        rst_n = 0;
        #10;
        rst_n = 1;
        #10;
        expected_sum = 0;
        test_data[0] = 8'd1;
        test_data[1] = 8'd2;
        test_data[2] = 8'd3;
        expected_sum = 8'd6;

        // Send data with out_ready toggling
        for (i = 0; i < 3; i = i + 1) begin
            @(posedge clk);
            #1;
            in_valid <= 1'b1;
            in_data <= test_data[i];
            if (i % 2 == 0) begin
                out_ready <= 1'b1;
            end else begin
                out_ready <= 1'b0;
            end
            wait (in_ready && in_valid);
            @(posedge clk);
            #1;
            in_valid <= 1'b0;
            in_data <= 8'b0;
        end
        // Assert out_ready to drain
        @(posedge clk);
        out_ready <= 1'b1;
        #10;
        @(posedge clk);
        #1;
        if (out_valid) begin
            result = out_data;
            if (result !== expected_sum) begin
                $display("Test 2 FAIL: Expected %d, got %d", expected_sum, result);
                pass = 1'b0;
            end else begin
                $display("Test 2 Pass: Accumulated = %d", result);
            end
        end else begin
            $display("Test 2 FAIL: No output");
            pass = 1'b0;
        end

        // Final report
        if (pass) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL");
        end
        #20;
        $finish;
    end

endmodule
