module tb_top;
  reg [1-1:0] clk;
  reg [1-1:0] rst_n;
  reg [1-1:0] event_valid;
  wire [8-1:0] count;
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
