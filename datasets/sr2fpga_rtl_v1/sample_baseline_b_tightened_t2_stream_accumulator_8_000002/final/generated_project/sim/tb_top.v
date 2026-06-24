module tb_top;
    reg clk;
    reg rst_n;
    reg in_valid;
    reg [7:0] in_data;
    wire out_ready;
    wire [7:0] sum;
    integer i;
    reg [7:0] expected_sum;
    reg [7:0] test_data [0:9];
    top dut (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .out_ready(out_ready),
        .sum(sum)
    );
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    initial begin
        $dumpfile("sim.vcd");
        $dumpvars(0, tb_top);
        rst_n = 0;
        in_valid = 0;
        in_data = 0;
        #20 rst_n = 1;
        expected_sum = 8'd0;
        test_data[0] = 8'd15;
        test_data[1] = 8'd27;
        test_data[2] = 8'd5;
        test_data[3] = 8'd42;
        test_data[4] = 8'd11;
        test_data[5] = 8'd8;
        test_data[6] = 8'd33;
        test_data[7] = 8'd1;
        test_data[8] = 8'd60;
        test_data[9] = 8'd14;
        for (i = 0; i < 10; i = i + 1) begin
            @(posedge clk);
            #1 in_valid = 1;
            in_data = test_data[i];
            expected_sum = expected_sum + test_data[i];
            @(posedge clk);
            #1 in_valid = 0;
        end
        #20;
        if (sum === expected_sum) begin
            $display("TEST_PASS");
            $finish;
        end else begin
            $display("TEST_FAIL: sum=%0d expected=%0d", sum, expected_sum);
            $finish;
        end
    end
endmodule
