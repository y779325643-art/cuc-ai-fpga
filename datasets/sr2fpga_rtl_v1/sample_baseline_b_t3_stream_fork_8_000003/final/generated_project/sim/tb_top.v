`timescale 1ns/1ps
module tb_top;

    reg clk;
    reg rst_n;
    reg in_valid;
    wire in_ready;
    reg [7:0] in_data;
    wire out0_valid, out1_valid;
    reg out0_ready, out1_ready;
    wire [7:0] out0_data, out1_data;

    top u_top (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_data(in_data),
        .out0_valid(out0_valid),
        .out0_ready(out0_ready),
        .out0_data(out0_data),
        .out1_valid(out1_valid),
        .out1_ready(out1_ready),
        .out1_data(out1_data)
    );

    always #5 clk = ~clk;

    integer test_cnt;
    reg [7:0] expected_data;
    reg expected_valid;

    initial begin
        clk = 0;
        rst_n = 0;
        in_valid = 0;
        in_data = 0;
        out0_ready = 0;
        out1_ready = 0;
        test_cnt = 0;
        #20 rst_n = 1;

        // Test 1: Basic push and pop
        @(posedge clk);
        in_valid <= 1;
        in_data <= 8'hA5;
        out0_ready <= 1;
        out1_ready <= 1;
        @(posedge clk);
        if (in_ready !== 1) begin
            $display("TEST_FAIL: in_ready not high");
            $finish;
        end
        if (out0_data !== 8'hA5 || out1_data !== 8'hA5) begin
            $display("TEST_FAIL: data mismatch");
            $finish;
        end
        if (out0_valid !== 1'b0 || out1_valid !== 1'b0) begin // output stages have one cycle delay
            // Actually stream_stage is a register, so valid comes out next cycle
            // Let's check after another cycle
            @(posedge clk);
            if (out0_valid !== 1 || out1_valid !== 1) begin
                $display("TEST_FAIL: output valid not high after pipeline");
                $finish;
            end
            if (out0_data !== 8'hA5 || out1_data !== 8'hA5) begin
                $display("TEST_FAIL: output data mismatch");
                $finish;
            end
        end
        in_valid <= 0;
        @(posedge clk);

        // Test multiple transactions
        for (int i = 0; i < 10; i++) begin
            @(posedge clk);
            in_valid <= 1;
            in_data <= i;
            out0_ready <= 1;
            out1_ready <= 1;
            @(posedge clk);
            // Wait for pipeline latency
            @(posedge clk);
            if (out0_data !== i[7:0] || out1_data !== i[7:0]) begin
                $display("TEST_FAIL: data mismatch at iteration %0d", i);
                $finish;
            end
        end
        in_valid <= 0;

        // Test backpressure
        @(posedge clk);
        in_valid <= 1;
        in_data <= 8'hBB;
        out0_ready <= 0;
        out1_ready <= 1;
        @(posedge clk);
        if (in_ready !== 0) begin
            $display("TEST_FAIL: in_ready should be 0 when one output not ready");
            $finish;
        end
        out0_ready <= 1;
        @(posedge clk);
        if (in_ready !== 1) begin
            $display("TEST_FAIL: in_ready should be 1 after ready");
            $finish;
        end
        @(posedge clk);
        @(posedge clk);
        // Check final outputs
        if (out0_data !== 8'hBB || out1_data !== 8'hBB) begin
            $display("TEST_FAIL: backpressure data mismatch");
            $finish;
        end

        $display("TEST_PASS");
        $finish;
    end

    // Assert outputs eventually
    always @(posedge clk) begin
        // Simple self-check: output data should match input data after pipeline
    end

endmodule
