`timescale 1ns/1ns
module tb_top;
    reg clk, rst_n;
    reg [7:0] in0_data, in1_data;
    reg in0_valid, in1_valid;
    wire in0_ready, in1_ready;
    wire [7:0] out_data;
    wire out_valid;
    reg out_ready;
    integer errors;
    
    top uut (
        .clk(clk), .rst_n(rst_n),
        .in0_valid(in0_valid), .in0_data(in0_data), .in0_ready(in0_ready),
        .in1_valid(in1_valid), .in1_data(in1_data), .in1_ready(in1_ready),
        .out_valid(out_valid), .out_data(out_data), .out_ready(out_ready)
    );
    
    always #5 clk = ~clk;
    
    initial begin
        clk = 0;
        rst_n = 0;
        in0_valid = 0; in1_valid = 0;
        out_ready = 1;
        errors = 0;
        #20 rst_n = 1;
        #10;
        
        // Test sequence
        // First pair: in0=1, in1=2 => sum=3, accumulator gets 3, output should be 3
        @(posedge clk);
        in0_valid = 1; in0_data = 8'd1;
        in1_valid = 1; in1_data = 8'd2;
        out_ready = 1;
        @(posedge clk);
        if (out_valid && out_data !== 8'd3) begin
            $display("ERROR: Expected 3, got %d", out_data);
            errors = errors + 1;
        end
        // Second pair: in0=3, in1=4 => sum=7, accumulated=3+7=10, output should be 10
        @(posedge clk);
        in0_valid = 1; in0_data = 8'd3;
        in1_valid = 1; in1_data = 8'd4;
        out_ready = 1;
        @(posedge clk);
        if (out_valid && out_data !== 8'd10) begin
            $display("ERROR: Expected 10, got %d", out_data);
            errors = errors + 1;
        end
        // Third pair: in0=5, in1=6 => sum=11, accumulated=10+11=21, output should be 21
        @(posedge clk);
        in0_valid = 1; in0_data = 8'd5;
        in1_valid = 1; in1_data = 8'd6;
        out_ready = 1;
        @(posedge clk);
        if (out_valid && out_data !== 8'd21) begin
            $display("ERROR: Expected 21, got %d", out_data);
            errors = errors + 1;
        end
        #100;
        if (errors === 0)
            $display("TEST_PASS");
        else
            $display("TEST_FAIL");
        $finish;
    end
endmodule
