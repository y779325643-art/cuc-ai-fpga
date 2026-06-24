module tb_top;
  reg clk;
  reg rst_n;
  reg [7:0] in0_data, in1_data;
  reg in0_valid, in1_valid;
  wire in0_ready, in1_ready;
  wire [7:0] out_data;
  wire out_valid;
  reg out_ready;
  integer error_count;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_valid(in0_valid),
    .in0_data(in0_data),
    .in0_ready(in0_ready),
    .in1_valid(in1_valid),
    .in1_data(in1_data),
    .in1_ready(in1_ready),
    .out_valid(out_valid),
    .out_data(out_data),
    .out_ready(out_ready)
  );
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end
  initial begin
    rst_n = 0;
    in0_valid = 0;
    in1_valid = 0;
    in0_data = 0;
    in1_data = 0;
    out_ready = 1;
    error_count = 0;
    #10 rst_n = 1;
    #10;
    // Test: feed values and check accumulation
    // Stream0: 1,2,3; Stream1: 10,20,30; join selects in0; accumulator sums
    in0_data = 8'd1; in0_valid = 1;
    in1_data = 8'd10; in1_valid = 1;
    #10;
    in0_data = 8'd2;
    in1_data = 8'd20;
    #10;
    in0_data = 8'd3;
    in1_data = 8'd30;
    #10;
    in0_valid = 0;
    in1_valid = 0;
    // Wait for output
    #50;
    // Expected: sum after three samples = 1+2+3 = 6
    if (out_valid && out_data == 8'd6) begin
      $display("TEST_PASS");
    end else begin
      $display("TEST_FAIL");
      $display("Expected 6, got %d", out_data);
    end
    #10;
    $finish;
  end
endmodule
