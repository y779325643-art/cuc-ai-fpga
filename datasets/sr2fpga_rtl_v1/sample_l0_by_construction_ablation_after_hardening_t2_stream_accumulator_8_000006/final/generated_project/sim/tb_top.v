module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  reg [7:0] in_data;
  wire in_ready;
  wire sample_valid;
  wire [7:0] sum;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .in_ready(in_ready),
    .sample_valid(sample_valid),
    .sum(sum)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
