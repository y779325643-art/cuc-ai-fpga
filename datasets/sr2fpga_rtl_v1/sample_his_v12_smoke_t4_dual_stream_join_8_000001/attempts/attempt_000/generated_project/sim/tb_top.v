`timescale 1ns/1ps

module tb_top;

reg clk;
reg rst_n;
reg [7:0] in0_data;
reg in0_valid;
wire in0_ready;
reg [7:0] in1_data;
reg in1_valid;
wire in1_ready;
wire [7:0] out_data;
wire out_valid;
reg out_ready;

top u_top (
    .clk(clk),
    .rst_n(rst_n),
    .in0_data(in0_data),
    .in0_valid(in0_valid),
    .in0_ready(in0_ready),
    .in1_data(in1_data),
    .in1_valid(in1_valid),
    .in1_ready(in1_ready),
    .out_data(out_data),
    .out_valid(out_valid),
    .out_ready(out_ready)
);

initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

integer test_failed = 0;
reg [7:0] expected_accum;
reg [7:0] sent_count;

task drive_inputs(input [7:0] d0, input [7:0] d1);
begin
    @(posedge clk);
    in0_data = d0;
    in0_valid = 1;
    in1_data = d1;
    in1_valid = 1;
    wait(in0_ready && in1_ready);
    @(posedge clk);
    in0_valid = 0;
    in1_valid = 0;
end
endtask

task check_output(input [7:0] expected);
begin
    @(posedge clk);
    wait(out_valid && out_ready);
    @(posedge clk);
    if (out_data !== expected) begin
        $display("TEST_FAIL: Expected %d, got %d at time %t", expected, out_data, $time);
        test_failed = 1;
    end else begin
        $display("PASS: Got %d as expected", out_data);
    end
end
endtask

initial begin
    // Initialize
    rst_n = 0;
    in0_data = 0;
    in0_valid = 0;
    in1_data = 0;
    in1_valid = 0;
    out_ready = 1;
    expected_accum = 0;
    sent_count = 0;
    #20;
    rst_n = 1;
    #20;

    // Test 1: Basic sequential
    $display("Test 1: Basic sequential");
    expected_accum = 0;
    drive_inputs(1, 2); // sum=3
    expected_accum = 3;
    check_output(expected_accum);
    drive_inputs(3, 4); // sum=7, accum=3+7=10
    expected_accum = 10;
    check_output(expected_accum);
    drive_inputs(5, 6); // sum=11, accum=10+11=21
    expected_accum = 21;
    check_output(expected_accum);

    // Test 2: Backpressure
    $display("Test 2: Backpressure");
    out_ready = 0;
    drive_inputs(10, 20); // sum=30, accum=21+30=51
    expected_accum = 51;
    #40;
    out_ready = 1;
    check_output(expected_accum);

    // Test 3: Overflow wrap
    $display("Test 3: Overflow wrap");
    expected_accum = 51;
    drive_inputs(200, 200); // sum=400 mod 256=144, accum=51+144=195
    expected_accum = 195;
    check_output(expected_accum);
    drive_inputs(100, 100); // sum=200, accum=195+200=395 mod 256=139
    expected_accum = 139;
    check_output(expected_accum);

    if (test_failed) begin
        $display("TEST_FAIL");
    end else begin
        $display("TEST_PASS");
    end
    $finish;
end

endmodule
