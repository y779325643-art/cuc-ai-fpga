`timescale 1ns/1ps

module tb_top;
    reg clk;
    reg rst_n;
    reg in_valid;
    reg [7:0] in_data;
    wire [7:0] sum;

    top uut (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .sum(sum)
    );

    always #5 clk = ~clk;

    integer i;
    reg [7:0] test_data [0:4];
    reg [7:0] expected_sums [0:4];
    integer timeout;
    integer passed;

    initial begin
        clk = 0;
        rst_n = 0;
        in_valid = 0;
        in_data = 0;
        passed = 1;

        test_data[0] = 8'd10;
        test_data[1] = 8'd20;
        test_data[2] = 8'd30;
        test_data[3] = 8'd40;
        test_data[4] = 8'd50;

        expected_sums[0] = 8'd10;
        expected_sums[1] = 8'd30;
        expected_sums[2] = 8'd60;
        expected_sums[3] = 8'd100;
        expected_sums[4] = 8'd150;

        repeat (5) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);

        for (i = 0; i < 5; i = i + 1) begin
            @(negedge clk);
            in_valid = 1'b1;
            in_data = test_data[i];
            @(posedge clk);
            @(negedge clk);
            in_valid = 1'b0;

            timeout = 0;
            while (sum != expected_sums[i]) begin
                @(negedge clk);
                timeout = timeout + 1;
                if (timeout > 100) begin
                    $display("TEST_FAIL: Timeout waiting for sum after sample %0d", i);
                    $finish;
                end
            end

            if (sum != expected_sums[i]) begin
                passed = 0;
                $display("TEST_FAIL at i=%0d, expected %0d, got %0d", i, expected_sums[i], sum);
            end
        end

        if (passed)
            $display("TEST_PASS");
        else
            $display("TEST_FAIL");
        $finish;
    end
endmodule
