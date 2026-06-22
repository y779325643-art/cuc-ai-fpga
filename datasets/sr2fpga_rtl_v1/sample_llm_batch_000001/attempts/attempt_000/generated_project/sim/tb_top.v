module tb_top;
    reg clk;
    reg rst_n;
    wire [5:0] count;
    integer i;
    reg fail;

    top u_top (.clk(clk), .rst_n(rst_n), .count(count));

    always #5 clk = ~clk;

    initial begin
        clk = 0;
        rst_n = 0;
        fail = 0;
        #10;
        rst_n = 1;
        @(posedge clk);
        for (i = 1; i <= 63; i = i + 1) begin
            @(posedge clk);
            if (count !== i) begin
                $display("TEST_FAIL: expected %d, got %d", i, count);
                fail = 1;
            end
        end
        @(posedge clk);
        if (count !== 0) begin
            $display("TEST_FAIL: expected 0 after wrap, got %d", count);
            fail = 1;
        end
        if (!fail)
            $display("TEST_PASS");
        $finish;
    end
endmodule
