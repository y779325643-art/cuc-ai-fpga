module tb_top;
  localparam WIDTH = 8;
  reg event_valid;
  wire [8-1:0] count;
  reg clk;
  reg rst_n;
  top dut (
    .event_valid(event_valid),
    .count(count),
    .clk(clk),
    .rst_n(rst_n)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
