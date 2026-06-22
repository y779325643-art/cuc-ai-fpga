`timescale 1ns/1ps

module tb_top;

reg clk;
reg rst_n;
wire [1:0] state;
wire out;

top uut (.clk(clk), .rst_n(rst_n), .state(state), .out(out));

initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

initial begin
    integer i;
    reg [1:0] expected_state;
    // Reset sequence
    rst_n = 0;
    #20;
    rst_n = 1;
    #10;
    // Check state after reset
    if (state !== 2'b00) begin
        $display("TEST_FAIL: after reset state not S0");
        $finish;
    end
    expected_state = 2'b00;
    @(posedge clk);
    #1;
    for (i=0; i<8; i=i+1) begin
        @(posedge clk);
        #1;
        if (state !== expected_state) begin
            $display("TEST_FAIL: at cycle %0d expected state %b got %b", i, expected_state, state);
            $finish;
        end
        case (expected_state)
            2'b00: expected_state = 2'b01;
            2'b01: expected_state = 2'b10;
            2'b10: expected_state = 2'b11;
            2'b11: expected_state = 2'b00;
        endcase
    end
    $display("TEST_PASS");
    $finish;
end

initial begin
    $dumpfile("tb_top.vcd");
    $dumpvars(0, tb_top);
end

endmodule
