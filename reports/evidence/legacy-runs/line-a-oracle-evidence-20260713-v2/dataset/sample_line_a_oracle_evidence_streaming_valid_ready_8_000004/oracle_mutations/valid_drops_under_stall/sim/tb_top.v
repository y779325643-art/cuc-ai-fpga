`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [7:0] in_data;
  wire out_valid;
  reg out_ready;
  wire [7:0] out_data;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_word;
    input [7:0] value;
    begin
      @(negedge clk);
      in_data = value;
      in_valid = 1'b1;
      while (in_ready !== 1'b1) begin
        @(negedge clk);
      end
      @(negedge clk);
      in_valid = 1'b0;
    end
  endtask

  task expect_word;
    input [7:0] value;
    begin
      while (out_valid !== 1'b1) begin
        @(posedge clk);
      end
      #1;
      if (out_data !== value) begin
        $display("TEST_FAIL expected output %0d got %0d", value, out_data);
        $finish;
      end
    end
  endtask

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_data = 8'd0;
    out_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    send_word(8'd18);
    expect_word(8'd18);
    @(posedge clk);
    #1;

    out_ready = 1'b0;
    send_word(8'd165);
    repeat (2) @(posedge clk);
    #1;
    if (out_valid !== 1'b1) begin
      $display("TEST_FAIL stalled output was not held valid");
      $finish;
    end
    out_ready = 1'b1;
    expect_word(8'd165);
    @(posedge clk);
    #1;

    $display("TEST_PASS");
    $finish;
  end
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
