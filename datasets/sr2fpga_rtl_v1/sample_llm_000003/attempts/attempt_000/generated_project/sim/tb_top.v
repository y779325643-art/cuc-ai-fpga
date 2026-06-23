module tb_top;
    reg clk;
    reg rst_n;
    reg en;
    wire [7:0] count;

    top uut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .count(count)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        $display("Starting test...");
        rst_n = 0;
        en = 0;
        #20;
        rst_n = 1;
        #10;
        en = 1;
        #200;
        if (count == 8'd20) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL: count = %d", count);
        end
        $finish;
    end
endmodule
