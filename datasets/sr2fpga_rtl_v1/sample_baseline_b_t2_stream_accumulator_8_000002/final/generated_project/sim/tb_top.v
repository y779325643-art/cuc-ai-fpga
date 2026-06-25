`timescale 1ns/1ps
module tb_top;
    reg clk;
    reg rst_n;
    reg in_valid;
    reg [7:0] in_data;
    wire [7:0] sum;

    top dut (.*);

    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        $display("Starting test...");
        rst_n = 0;
        in_valid = 0;
        in_data = 0;
        #15;
        rst_n = 1;
        #10;
        @(posedge clk);
        in_valid = 1;
        in_data = 8'd1;
        @(posedge clk);
        in_data = 8'd2;
        @(posedge clk);
        in_data = 8'd3;
        @(posedge clk);
        in_data = 8'd4;
        @(posedge clk);
        in_data = 8'd5;
        @(posedge clk);
        in_valid = 0;
        #40;
        if (sum === 8'd15) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL: sum=%0d", sum);
        end
        $finish;
    end
endmodule
