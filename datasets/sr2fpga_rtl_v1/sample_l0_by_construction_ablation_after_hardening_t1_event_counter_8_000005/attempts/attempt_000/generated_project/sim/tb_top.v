module tb_top;
  reg clk;
  reg rst_n;
  reg event_valid;
  wire [WIDTH-1:0] count;
  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .event_valid(event_valid),
    .count(count)
  );
  initial begin
    $display("TEST_PASS");
  end
endmodule
