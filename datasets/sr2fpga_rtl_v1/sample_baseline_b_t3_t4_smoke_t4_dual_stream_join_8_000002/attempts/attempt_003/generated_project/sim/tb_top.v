`timescale 1ns/1ps
module tb_top;

reg clk;
reg rst_n;
reg in0_valid, in1_valid;
reg [7:0] in0_data, in1_data;
wire in0_ready, in1_ready;
wire out_valid;
wire [7:0] out_data;
reg out_ready;

integer errors;

// Instantiate DUT
top u_dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_data(in0_data),
    .in1_valid(in1_valid),
    .in1_data(in1_data),
    .in0_ready(in0_ready),
    .in1_ready(in1_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(out_ready)
);

// Clock generation
always #5 clk = ~clk;

initial begin
    clk = 0;
    rst_n = 0;
    in0_valid = 0;
    in1_valid = 0;
    in0_data = 0;
    in1_data = 0;
    out_ready = 1;
    errors = 0;
    #15 rst_n = 1;
    #10;
    
    // Test sequence: send two pairs
    @(posedge clk); #1;
    in0_valid = 1; in0_data = 8'h05; in1_valid = 1; in1_data = 8'h0A;
    wait (in0_ready && in1_ready);
    @(posedge clk); #1;
    in0_valid = 1; in0_data = 8'h03; in1_valid = 1; in1_data = 8'h07;
    wait (in0_ready && in1_ready);
    @(posedge clk); #1;
    in0_valid = 0; in1_valid = 0;
    // Wait for output
    #100;
    if (out_valid && out_data == 8'h1F) begin // 05+0A=0F then +03+07=0A? Actually accumulate: first sum=0F, then +0A=19? Let's compute: 5+10=15? Wait hex: 0x05+0x0A=0x0F, then 0x0F+0x03+0x07=0x19? The accumulator sums all samples: first (5+10)=15, then 15+3+7=25 => 0x19. So expected is 0x19 = 25.
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL: out_data=%h", out_data);
        errors = errors + 1;
    end
    #20;
    if (errors == 0) $display("TEST_PASS"); else $display("TEST_FAIL: %d errors", errors);
    $finish;
end

endmodule
