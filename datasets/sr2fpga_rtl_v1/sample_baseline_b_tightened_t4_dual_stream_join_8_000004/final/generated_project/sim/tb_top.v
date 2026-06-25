`timescale 1ns/1ns
module tb_top;

reg clk;
reg rst_n;
reg in0_valid, in1_valid;
reg [7:0] in0_data, in1_data;
wire out_valid;
wire [15:0] out_data;
wire in0_ready, in1_ready;

top u_top (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_data(in0_data),
    .in0_ready(in0_ready),
    .in1_valid(in1_valid),
    .in1_data(in1_data),
    .in1_ready(in1_ready),
    .out_valid(out_valid),
    .out_data(out_data)
);

always #5 clk = ~clk;

initial begin
    clk = 0;
    rst_n = 0;
    in0_valid = 0; in0_data = 0;
    in1_valid = 0; in1_data = 0;
    #10 rst_n = 1;
    #10;
    // test sequence
    @(posedge clk);
    in0_valid = 1; in0_data = 8'h01;
    in1_valid = 1; in1_data = 8'h02;
    @(posedge clk);
    in0_valid = 0; in1_valid = 0;
    wait(out_valid);
    @(posedge clk);
    #1;
    if (out_data == 16'h0102) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL");
    end
    #20;
    $finish;
end

endmodule
