module tb_top;

reg clk;
reg rst_n;
reg event_valid;
wire [7:0] count;

integer events = 0;
integer i;

top u_top (
  .clk(clk),
  .rst_n(rst_n),
  .event_valid(event_valid),
  .count(count)
);

always #5 clk = ~clk;

initial begin
  clk = 0;
  rst_n = 0;
  event_valid = 0;
  #20 rst_n = 1;
  #10;
  // Send 5 events
  for (i = 0; i < 5; i = i + 1) begin
    event_valid = 1;
    #10;
    event_valid = 0;
    #10;
    events = events + 1;
  end
  #30;
  // Check count
  if (count == events) begin
    $display("TEST_PASS");
  end else begin
    $display("TEST_FAIL");
  end
  #10 $finish;
end

endmodule
