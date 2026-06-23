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
    rst_n = 0;
    en = 0;
    #10;
    rst_n = 1;
    #10;
    en = 1;
    #100;
    if (count == 8'd10) begin
        $display("TEST_PASS");
        $finish;
    end else begin
        $display("TEST_FAIL at %0t: count = %d", $time, count);
        $finish;
    end
end

endmodule
