`timescale 1ns / 1ps

module tb_top;

reg clk, rst_n;
reg in0_valid, in1_valid;
wire in0_ready, in1_ready;
reg [7:0] in0_data, in1_data;
wire out_valid;
reg out_ready;
wire [7:0] out_data;

top #(8) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_ready(in0_ready),
    .in0_data(in0_data),
    .in1_valid(in1_valid),
    .in1_ready(in1_ready),
    .in1_data(in1_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
);

always begin
    clk = 0;
    #5 clk = 1;
    #5;
end

reg [7:0] in0_mem [0:9];
reg [7:0] in1_mem [0:9];
reg [7:0] expected [0:9];
integer i;
integer error_count;

initial begin
    error_count = 0;
    in0_mem[0] = 8'd1; in1_mem[0] = 8'd2; expected[0] = 8'd3;
    in0_mem[1] = 8'd3; in1_mem[1] = 8'd4; expected[1] = 8'd7;
    in0_mem[2] = 8'd5; in1_mem[2] = 8'd6; expected[2] = 8'd11;
    in0_mem[3] = 8'd7; in1_mem[3] = 8'd8; expected[3] = 8'd15;
    in0_mem[4] = 8'd9; in1_mem[4] = 8'd10; expected[4] = 8'd19;
    in0_mem[5] = 8'd2; in1_mem[5] = 8'd3; expected[5] = 8'd5;
    in0_mem[6] = 8'd4; in1_mem[6] = 8'd5; expected[6] = 8'd9;
    in0_mem[7] = 8'd6; in1_mem[7] = 8'd7; expected[7] = 8'd13;
    in0_mem[8] = 8'd8; in1_mem[8] = 8'd9; expected[8] = 8'd17;
    in0_mem[9] = 8'd10; in1_mem[9] = 8'd11; expected[9] = 8'd21;

    $display("Applying reset...");
    rst_n = 0;
    in0_valid = 0; in1_valid = 0;
    out_ready = 1;
    #20 rst_n = 1;
    #10;

    $display("Test 1: Normal operation");
    for (i=0; i<5; i=i+1) begin
        drive_pair(in0_mem[i], in1_mem[i], 100);
        check_output(expected[i], 100);
    end

    $display("Test 2: Backpressure on output");
    out_ready = 0;
    for (i=5; i<8; i=i+1) begin
        drive_pair(in0_mem[i], in1_mem[i], 100);
    end
    #20 out_ready = 1;
    for (i=5; i<8; i=i+1) begin
        check_output(expected[i], 100);
    end

    $display("Test 3: Input backpressure");
    out_ready = 1;
    drive_pair(in0_mem[8], in1_mem[8], 100);
    drive_pair(in0_mem[9], in1_mem[9], 100);
    // Attempt a third pair to see backpressure (skid buffer depth=2, so deep enough)
    in0_data = 8'hFF; in1_data = 8'hFF;
    in0_valid = 1; in1_valid = 1;
    @(negedge clk);
    if (in0_ready && in1_ready) begin
        // accepted, nothing to check
    end else begin
        $display("TEST_INFO: Backpressure detected on input");
    end
    in0_valid = 0; in1_valid = 0;
    check_output(expected[8], 100);
    check_output(expected[9], 100);
    // consume extra if any
    if (out_valid && out_ready) begin
        #10; // ignore
    end

    $display("Test 4: Reset");
    rst_n = 0;
    #20 rst_n = 1;
    #10;
    drive_pair(8'd1, 8'd1, 100);
    check_output(8'd2, 100);

    if (error_count == 0) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL: %0d errors", error_count);
    end
    $finish;
end

task drive_pair(input [7:0] d0, input [7:0] d1, input int timeout);
begin
    in0_data = d0;
    in1_data = d1;
    in0_valid = 1;
    in1_valid = 1;
    @(negedge clk);
    for (int k=0; k<timeout; k++) begin
        if (in0_ready && in1_ready) begin
            in0_valid = 0;
            in1_valid = 0;
            return;
        end
        @(negedge clk);
    end
    $display("TEST_FAIL: timeout in drive_pair");
    error_count++;
    $finish;
end
endtask

task check_output(input [7:0] exp, input int timeout);
begin
    @(negedge clk);
    for (int k=0; k<timeout; k++) begin
        if (out_valid && out_ready) begin
            if (out_data !== exp) begin
                $display("TEST_FAIL: expected %0d, got %0d", exp, out_data);
                error_count++;
            end else begin
                $display("TEST_INFO: correct %0d", out_data);
            end
            return;
        end
        @(negedge clk);
    end
    $display("TEST_FAIL: timeout in check_output");
    error_count++;
    $finish;
end
endtask

endmodule
