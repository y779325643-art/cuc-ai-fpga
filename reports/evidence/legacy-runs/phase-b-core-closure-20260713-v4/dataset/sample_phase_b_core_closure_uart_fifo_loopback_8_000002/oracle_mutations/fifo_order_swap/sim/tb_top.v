`timescale 1ns/1ps

module tb_top;
  localparam integer CLKS_PER_BIT = 4;
  reg clk;
  reg rst_n;
  reg rx;
  reg tx_enable;
  wire tx;

  top #(.CLKS_PER_BIT(CLKS_PER_BIT)) uut (
    .clk(clk),
    .rst_n(rst_n),
    .rx(rx),
    .tx(tx),
    .tx_enable(tx_enable)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_uart_byte;
    input [7:0] value;
    integer bit_index;
    begin
      @(negedge clk);
      rx = 1'b0;
      repeat (CLKS_PER_BIT) @(posedge clk);
      for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
        rx = value[bit_index];
        repeat (CLKS_PER_BIT) @(posedge clk);
      end
      rx = 1'b1;
      repeat (CLKS_PER_BIT) @(posedge clk);
    end
  endtask

  task expect_tx_byte;
    input [7:0] expected;
    reg [7:0] observed;
    integer bit_index;
    begin
      @(negedge tx);
      repeat (CLKS_PER_BIT + (CLKS_PER_BIT / 2)) @(posedge clk);
      for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
        observed[bit_index] = tx;
        repeat (CLKS_PER_BIT) @(posedge clk);
      end
      if (tx !== 1'b1 || observed !== expected) begin
        $display("TEST_FAIL expected TX byte=%h got=%h", expected, observed);
        $finish;
      end
    end
  endtask

  initial begin
    rst_n = 1'b0;
    rx = 1'b1;
    tx_enable = 1'b0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    send_uart_byte(8'h12);
    send_uart_byte(8'h34);
    send_uart_byte(8'h56);
    send_uart_byte(8'h78);

    fork
      begin
        tx_enable = 1'b1;
        send_uart_byte(8'h9a);
        send_uart_byte(8'hbc);
      end
      begin
        expect_tx_byte(8'h12);
        expect_tx_byte(8'h34);
        expect_tx_byte(8'h56);
        expect_tx_byte(8'h78);
        expect_tx_byte(8'h9a);
        expect_tx_byte(8'hbc);
      end
    join

    $display("TEST_PASS");
    $finish;
  end
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
