module tb_top;

    reg clk;
    reg rst_n;
    reg [7:0] in0_data, in1_data;
    reg in0_valid, in1_valid;
    wire in0_ready, in1_ready;
    wire out_valid;
    wire [15:0] out_data;
    reg out_ready;

    top dut (
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

    initial clk = 0;
    always #5 clk = ~clk;

    integer test_fail = 0;
    integer cycle;
    reg [15:0] expected_accum = 0;
    reg [7:0] test_data0 [0:1];
    reg [7:0] test_data1 [0:1];

    initial begin
        // Initialize
        rst_n = 0;
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 0;
        in0_data = 0;
        in1_data = 0;
        #20;
        rst_n = 1;
        #10;

        // Test data
        test_data0[0] = 8'd10;
        test_data1[0] = 8'd5;
        test_data0[1] = 8'd20;
        test_data1[1] = 8'd30;

        // Send first pair
        @(posedge clk);
        in0_valid = 1; in0_data = test_data0[0];
        in1_valid = 1; in1_data = test_data1[0];
        out_ready = 1;
        @(posedge clk);
        // Wait for handshake
        while (!in0_ready || !in1_ready) @(posedge clk);
        in0_valid = 0; in1_valid = 0;
        // Wait for output
        while (!out_valid) @(posedge clk);
        expected_accum = test_data0[0] + test_data1[0];
        if (out_data !== expected_accum) begin
            $display("TEST_FAIL: Expected %0d, got %0d", expected_accum, out_data);
            test_fail = 1;
        end
        @(posedge clk);
        // Send second pair
        in0_valid = 1; in0_data = test_data0[1];
        in1_valid = 1; in1_data = test_data1[1];
        @(posedge clk);
        while (!in0_ready || !in1_ready) @(posedge clk);
        in0_valid = 0; in1_valid = 0;
        while (!out_valid) @(posedge clk);
        expected_accum = (test_data0[0] + test_data1[0]) + (test_data0[1] + test_data1[1]);
        if (out_data !== expected_accum) begin
            $display("TEST_FAIL: Expected %0d, got %0d", expected_accum, out_data);
            test_fail = 1;
        end
        @(posedge clk);

        if (test_fail) begin
            $display("TEST_FAIL");
        end else begin
            $display("TEST_PASS");
        end
        #100 $finish;
    end

endmodule
