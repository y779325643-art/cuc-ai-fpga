module tb_top;
    reg clk;
    reg rst_n;
    reg start;
    reg [7:0] data;
    wire tx;
    wire tx_busy;
    integer sim_time;
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100 MHz
    end
    initial begin
        rst_n = 0;
        #20 rst_n = 1;
        #10;
        data = 8'h55; // alternating bits
        start = 1;
        #10 start = 0;
        wait (tx_busy == 0);
        #1000;
        if (tx_busy == 0) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL");
        end
        $finish;
    end
    initial begin
        #2000;
        $display("TEST_FAIL (timeout)");
        $finish;
    end
    top uut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .data(data),
        .tx(tx),
        .tx_busy(tx_busy)
    );
endmodule
