module tb_top;
    reg clk, rst_n, en;
    wire [7:0] count;
    top uut (.clk(clk), .rst_n(rst_n), .en(en), .count(count));
    initial clk = 0;
    always #5 clk = ~clk;
    reg [7:0] expected;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) expected <= 0;
        else if (en) expected <= expected + 1;
    end
    always @(posedge clk) begin
        if (rst_n && count !== expected) begin
            $display("Mismatch at %0t: count=%d expected=%d", $time, count, expected);
            $finish;
        end
    end
    initial begin
        $display("Starting test");
        rst_n = 0; en = 0;
        #20 rst_n = 1;
        #10 en = 1;
        #100 en = 0;
        #30 en = 1;
        #200;
        $display("TEST_PASS");
        $finish;
    end
endmodule
