module tb_top;

reg clk;
reg rst_n;
reg start;
reg [7:0] data_in;
wire sclk;
wire mosi;
wire cs_n;
wire busy;
wire done;

top uut (
    .clk(clk),
    .rst_n(rst_n),
    .start(start),
    .data_in(data_in),
    .sclk(sclk),
    .mosi(mosi),
    .cs_n(cs_n),
    .busy(busy),
    .done(done)
);

initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

initial begin
    rst_n = 0;
    start = 0;
    data_in = 8'hA5;
    #20 rst_n = 1;
    #100;
    @(posedge clk);
    start = 1;
    @(posedge clk);
    start = 0;
    wait(done);
    #100;
    if (cs_n === 1 && busy === 0) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL");
    end
    $finish;
end

endmodule
