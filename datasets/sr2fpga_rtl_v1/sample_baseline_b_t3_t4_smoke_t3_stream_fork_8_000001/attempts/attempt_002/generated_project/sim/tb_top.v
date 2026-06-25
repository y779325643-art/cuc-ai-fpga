module tb_top;

reg clk, rst_n;
reg [7:0] in_data;
reg in_valid;
wire in_ready;
wire [7:0] out0_data, out1_data;
wire out0_valid, out1_valid;
reg out0_ready, out1_ready;

integer i, errors;
reg [7:0] test_data [0:9];

initial begin
    $dumpfile("tb_top.vcd");
    $dumpvars(0, tb_top);
    errors = 0;
    clk = 0;
    rst_n = 0;
    in_valid = 0;
    out0_ready = 0;
    out1_ready = 0;
    #10 rst_n = 1;
    // load test data
    for (i = 0; i < 10; i = i+1) test_data[i] = i;
    // drive inputs
    for (i = 0; i < 10; i = i+1) begin
        @(posedge clk);
        in_data <= test_data[i];
        in_valid <= 1;
        out0_ready <= 1;
        out1_ready <= 1;
        wait(in_ready);
        @(posedge clk);
        in_valid <= 0;
        wait(out0_valid && out1_valid);
        @(posedge clk);
        if (out0_data !== test_data[i] || out1_data !== test_data[i]) begin
            $display("Mismatch at %0d: expected %0d, got out0=%0d out1=%0d", i, test_data[i], out0_data, out1_data);
            errors = errors + 1;
        end
    end
    // finish
    #50;
    if (errors == 0)
        $display("TEST_PASS");
    else
        $display("TEST_FAIL");
    $finish;
end

always #5 clk = ~clk;

top u_top (
    .clk(clk),
    .rst_n(rst_n),
    .in_data(in_data),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .out0_data(out0_data),
    .out0_valid(out0_valid),
    .out0_ready(out0_ready),
    .out1_data(out1_data),
    .out1_valid(out1_valid),
    .out1_ready(out1_ready)
);

endmodule
