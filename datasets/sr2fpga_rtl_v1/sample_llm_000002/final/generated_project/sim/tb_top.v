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
        #10;
        rst_n = 1;
        #10;
        en = 1;
        #20;
        if (count == 8'd2) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL: count = %d", count);
        end
        #10;
        $finish;
    end
endmodule