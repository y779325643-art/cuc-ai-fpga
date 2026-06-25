`timescale 1ns/1ps
module tb_top;
reg clk, rst_n;
reg [7:0] s_axis0_tdata, s_axis1_tdata;
reg s_axis0_tvalid, s_axis1_tvalid;
wire s_axis0_tready, s_axis1_tready;
wire [7:0] m_axis_tdata;
wire m_axis_tvalid;
reg m_axis_tready;

top #(.WIDTH(8)) dut (.*);

initial clk = 0;
always #5 clk = ~clk;

integer errors;

task wait_for_output;
input [7:0] expected;
output reg [7:0] data;
integer wait_cnt;
begin
    wait_cnt = 0;
    while (wait_cnt < 20) begin
        @(posedge clk);
        if (m_axis_tvalid && m_axis_tready) begin
            data = m_axis_tdata;
            if (data !== expected) begin
                $display("TEST_FAIL: Expected %0d, got %0d at time %0t", expected, data, $time);
                errors = errors + 1;
            end
            return;
        end
        wait_cnt = wait_cnt + 1;
    end
    $display("TEST_FAIL: Timeout at time %0t", $time);
    errors = errors + 1;
end
endtask

initial begin
    errors = 0;
    rst_n = 0;
    s_axis0_tvalid = 0;
    s_axis1_tvalid = 0;
    m_axis_tready = 0;
    @(posedge clk);
    #1 rst_n = 1;
    @(posedge clk);
    // First pair: 1+2=3, accumulator: 3
    s_axis0_tdata = 1; s_axis0_tvalid = 1;
    s_axis1_tdata = 2; s_axis1_tvalid = 1;
    m_axis_tready = 1;
    @(posedge clk);
    s_axis0_tvalid = 0; s_axis1_tvalid = 0;
    wait_for_output(3, ); // ignore output data
    // Second pair: 3+4=7, accumulator: 3+7=10
    s_axis0_tdata = 3; s_axis0_tvalid = 1;
    s_axis1_tdata = 4; s_axis1_tvalid = 1;
    @(posedge clk);
    s_axis0_tvalid = 0; s_axis1_tvalid = 0;
    wait_for_output(10, );
    // Third pair: 5+6=11, accumulator: 10+11=21
    s_axis0_tdata = 5; s_axis0_tvalid = 1;
    s_axis1_tdata = 6; s_axis1_tvalid = 1;
    @(posedge clk);
    s_axis0_tvalid = 0; s_axis1_tvalid = 0;
    wait_for_output(21, );
    
    if (errors == 0) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL: %0d errors", errors);
    end
    $finish;
end
endmodule
