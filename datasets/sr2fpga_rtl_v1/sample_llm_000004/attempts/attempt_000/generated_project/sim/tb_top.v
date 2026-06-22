module tb_top;

reg clk;
reg reset_n;
reg en;
wire [7:0] q;

top uut (
    .clk(clk),
    .reset_n(reset_n),
    .en(en),
    .q(q)
);

initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

initial begin
    // Test sequence
    reset_n = 0;
    en = 0;
    #20;
    reset_n = 1;
    #10;
    if (q !== 8'd0) begin
        $display("FAIL: q should be 0 after reset");
        $finish;
    end
    en = 1;
    #10;
    if (q !== 8'd1) begin
        $display("FAIL: q should be 1 after first enable");
        $finish;
    end
    #90; // wait for 9 more clocks, total 10 clocks
    if (q !== 8'd10) begin
        $display("FAIL: q should be 10 after 10 clocks");
        $finish;
    end
    en = 0;
    #20;
    if (q !== 8'd10) begin
        $display("FAIL: q should stay 10 when en=0");
        $finish;
    end
    reset_n = 0;
    #10;
    if (q !== 8'd0) begin
        $display("FAIL: q should be 0 after reset");
        $finish;
    end
    $display("TEST_PASS");
    $finish;
end

endmodule
